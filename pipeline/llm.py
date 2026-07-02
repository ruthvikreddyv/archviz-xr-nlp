import json, os, re, time, random
from dotenv import load_dotenv
from groq import Groq
from pipeline.graph_cleaner import clean_graph
load_dotenv()

MODEL = "llama-3.1-8b-instant"
MAX_CONCEPTS = 45
MAX_EDGES = 90
MAX_RETRIES = 3
VALID_TYPES = {"component","process","data","named_entity"}
STOP_WORDS = {"a","an","and","of","the","in","on","at","by","for","to","is","are","was","were","be","been","with"}

def get_client():
    k=os.getenv("GROQ_API_KEY")
    if not k: raise ValueError("GROQ_API_KEY not set")
    return Groq(api_key=k)

def make_id(text):
    nid=re.sub(r"[^a-z0-9]+","_",str(text).lower()).strip("_"); return nid or "concept"

def guess_type(label,current="component"):
    if current in VALID_TYPES: return current
    t=label.lower()
    if any(w in t for w in ["token","output","input","embedding","vector","data","matrix","tensor"]): return "data"
    if any(w in t for w in ["attention","norm","softmax","activation","encoding","pooling","feed"]): return "process"
    return "component"

def _token_set(text):
    return {t for t in re.findall(r"[a-z0-9]+",text.lower()) if t not in STOP_WORDS}

def is_supported_label(label,entities,ocr_text=""):
    lt=_token_set(label)
    if not lt: return False
    et={t for e in entities for t in _token_set(str(e.get("label","")))}
    ot=_token_set(ocr_text) if ocr_text else set()
    src=et|ot
    if not src: return False
    ratio=len(lt&src)/len(lt)
    threshold=0.7 if len(src)<15 else 0.5
    return ratio>=threshold

def fallback_result(entities,relations,reason=""):
    nodes=[]; seen=set()
    for e in entities[:MAX_CONCEPTS]:
        label=e.get("label") or e.get("id") or "Concept"
        nid=make_id(e.get("id") or label)
        if not nid or nid in seen: continue
        seen.add(nid); nodes.append({"id":nid,"label":str(label),"type":guess_type(str(label),e.get("type","component"))})
    nids={n["id"] for n in nodes}; edges=[]; seen_e=set()
    for r in relations[:MAX_EDGES]:
        s=make_id(r.get("from","")); t=make_id(r.get("to",""))
        k=(s,t)
        if s in nids and t in nids and s!=t and k not in seen_e:
            seen_e.add(k); edges.append({"from":s,"to":t,"label":r.get("label","related_to")})
    return clean_graph({"nodes":nodes,"edges":edges,
        "explanation":"Knowledge graph of extracted concepts.",
        "quiz":[{"q":"What does each sphere represent?","options":["A concept","A file","A database","A camera"],"answer":0},
                {"q":"What do lines represent?","options":["Visual style","Relationships","Pixels","Answers"],"answer":1},
                {"q":"Why visual extraction?","options":["Extract from diagram","Render WebXR","Start server","Install packages"],"answer":0}]})

def build_prompt(entities,relations,ocr_text="",error_hint=""):
    labels=[e["label"] for e in entities[:MAX_CONCEPTS]]
    rels=[f"{r['from']} --{r['label']}--> {r['to']}" for r in relations[:MAX_EDGES]]
    ctx=f"\nRaw OCR text:\n{ocr_text[:1500]}\n" if ocr_text else ""
    err=f"\nPREVIOUS FAILED: {error_hint}\nFix before returning.\n" if error_hint else ""
    return f"""You analyse academic diagrams and return structured JSON.{err}
Concepts: {json.dumps(labels)}
Relations: {chr(10).join(rels) if rels else "None — infer from concepts."}
{ctx}
Return ONE JSON object:
{{"nodes":[{{"id":"snake_case","label":"Human Label","type":"component"}}],
"edges":[{{"from":"id","to":"id","label":"verb"}}],
"explanation":"Two sentences.","quiz":[{{"q":"?","options":["A","B","C","D"],"answer":0}}]}}
Rules: types=component|process|data|named_entity. Max {MAX_CONCEPTS} nodes {MAX_EDGES} edges.
Use ONLY concepts from the list above. 3 quiz questions. JSON only."""

def parse_response(text):
    t=text.strip().replace("```json","").replace("```","").strip()
    s,e=t.find("{"),t.rfind("}")+1
    if s==-1 or e<=s: raise ValueError("No JSON found")
    return json.loads(t[s:e])

def validate_result(result,entities,relations,ocr_text=""):
    for f in ["nodes","edges","explanation","quiz"]:
        if f not in result: raise ValueError(f"Missing {f}")
    nodes=[]; seen=set()
    for node in result.get("nodes",[])[:MAX_CONCEPTS]:
        label=str(node.get("label") or node.get("id") or "Concept")
        if not is_supported_label(label,entities,ocr_text): continue
        nid=make_id(node.get("id") or label)
        if not nid or nid in seen: continue
        seen.add(nid); nodes.append({"id":nid,"label":label,"type":guess_type(label,node.get("type","component"))})
    if not nodes: raise ValueError("No valid nodes returned")
    nids={n["id"] for n in nodes}; edges=[]; seen_e=set()
    for edge in result.get("edges",[]):
        s=make_id(edge.get("from","")); t=make_id(edge.get("to",""))
        lbl=str(edge.get("label","related_to")); key=(s,t,lbl)
        if s in nids and t in nids and s!=t and key not in seen_e:
            seen_e.add(key); edges.append({"from":s,"to":t,"label":lbl})
    quiz=[]
    for item in result.get("quiz",[])[:3]:
        opts=item.get("options",[]); ans=item.get("answer",0)
        if isinstance(opts,list) and len(opts)==4 and isinstance(ans,int) and 0<=ans<=3:
            quiz.append({"q":str(item.get("q","?")), "options":[str(o) for o in opts],"answer":ans})
    fb=fallback_result(entities,relations)
    while len(quiz)<3: quiz.append(fb["quiz"][len(quiz)])
    return clean_graph({"nodes":nodes,"edges":edges or fb["edges"],
                        "explanation":str(result.get("explanation",fb["explanation"])),"quiz":quiz})

def generate(entities,relations,ocr_text=""):
    if not entities: raise ValueError("No entities provided")
    ents=entities[:MAX_CONCEPTS]; rels=relations[:MAX_EDGES]
    print(f"[LLM] Calling Groq ({MODEL}) with {len(ents)} concepts...")
    last=""
    for attempt in range(1,MAX_RETRIES+1):
        if attempt>1:
            wait=2**(attempt-2)+random.uniform(0,0.5)
            print(f"[LLM] Retry {attempt}/{MAX_RETRIES} (wait {wait:.1f}s)..."); time.sleep(wait)
        try:
            client=get_client()
            prompt=build_prompt(ents,rels,ocr_text,last)
            resp=client.chat.completions.create(model=MODEL,temperature=0.1,max_tokens=6000,
                messages=[{"role":"system","content":"You are a JSON-only API. Return one valid JSON object. No markdown."},
                          {"role":"user","content":prompt}])
            raw=resp.choices[0].message.content
            result=validate_result(parse_response(raw),ents,rels,ocr_text)
            print(f"[LLM] OK {len(result['nodes'])} nodes, {len(result['edges'])} edges (attempt {attempt})")
            return result
        except Exception as exc:
            last=str(exc); print(f"[LLM] Attempt {attempt} failed: {exc}")
    print(f"[LLM] All attempts failed — using fallback")
    return fallback_result(ents,rels,last)