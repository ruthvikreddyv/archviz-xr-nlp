import os

REPO = os.path.dirname(os.path.abspath(__file__))

files = {}

# ── 1. pipeline/vlm.py ───────────────────────────────────────
files["pipeline/vlm.py"] = '''
import base64, json, os, re, time, random
from typing import Optional
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, field_validator, model_validator
from pipeline.graph_cleaner import clean_graph
load_dotenv()

VISION_MODELS = [
    m for m in [
        os.getenv("ARCHVIZ_VLM_MODEL",""),
        "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-preview",
    ] if m
]
MAX_RETRIES = 3
VALID_TYPES = {"component","process","data","named_entity"}

class VLMNode(BaseModel):
    id: str; label: str; type: str = "component"; confidence: float = 0.9
    @field_validator("id")
    @classmethod
    def norm(cls,v):
        n=re.sub(r"[^a-z0-9]+","_",v.lower()).strip("_"); return n or "concept"
    @field_validator("type")
    @classmethod
    def vtype(cls,v): return v if v in VALID_TYPES else "component"
    @field_validator("confidence")
    @classmethod
    def clamp(cls,v): return max(0.0,min(1.0,v))

class VLMEdge(BaseModel):
    from_node: str; to_node: str; label: str="related_to"; confidence: float=0.85
    @field_validator("from_node","to_node")
    @classmethod
    def norm(cls,v): return re.sub(r"[^a-z0-9]+","_",v.lower()).strip("_")
    @field_validator("confidence")
    @classmethod
    def clamp(cls,v): return max(0.0,min(1.0,v))

class VLMQuiz(BaseModel):
    q: str; options: list[str]; answer: int
    @field_validator("options")
    @classmethod
    def four(cls,v):
        assert len(v)==4,"Quiz needs 4 options"; return [str(o) for o in v]

class VLMResult(BaseModel):
    nodes: list[VLMNode]; edges: list[VLMEdge]
    explanation: str; quiz: list[VLMQuiz]; diagram_type: str="unknown"
    @model_validator(mode="after")
    def fix(self):
        ids={n.id for n in self.nodes}
        self.edges=[e for e in self.edges if e.from_node!=e.to_node and e.from_node in ids and e.to_node in ids]
        while len(self.quiz)<3:
            self.quiz.append(VLMQuiz(q="What does this diagram show?",options=["A knowledge graph","A spreadsheet","A database","A network"],answer=0))
        self.quiz=self.quiz[:3]; return self

SYSTEM="You are a diagram analysis API. Return ONLY valid JSON, no markdown."

def _prompt(ctx=None,err=""):
    e=f"PREVIOUS FAILED: {err}. Fix before returning.\\n" if err else ""
    c=f"PDF text context:\\n{ctx[:1200]}\\n" if ctx else ""
    return f"""{e}Analyse the diagram image. Return exactly:
{{"nodes":[{{"id":"snake_case","label":"Exact label","type":"component|process|data|named_entity","confidence":0.95}}],
"edges":[{{"from_node":"id","to_node":"id","label":"verb","confidence":0.85}}],
"explanation":"Two sentences about this diagram.",
"quiz":[{{"q":"Question?","options":["A","B","C","D"],"answer":0}}],
"diagram_type":"hierarchical|network|flowchart|unknown"}}
Rules: ONLY extract what is visually visible. No hallucination. Exactly 3 quiz items. JSON only.
{c}"""

def _call(b64,ctx,model,err=""):
    client=Groq(api_key=os.getenv("GROQ_API_KEY",""))
    r=client.chat.completions.create(model=model,temperature=0.1,max_tokens=4096,
        messages=[{"role":"system","content":SYSTEM},
                  {"role":"user","content":[{"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}},{"type":"text","text":_prompt(ctx,err)}]}])
    return r.choices[0].message.content

def _parse(raw):
    t=raw.strip().replace("```json","").replace("```","").strip()
    s,e=t.find("{"),t.rfind("}")+1
    if s==-1 or e<=s: raise ValueError("No JSON found")
    return json.loads(t[s:e])

def _fallback(reason):
    return {"nodes":[{"id":"diagram","label":"Diagram","type":"component","x":0,"y":0,"z":0,"confidence":0},
                     {"id":"failed","label":"Analysis Failed","type":"component","x":1,"y":0,"z":0,"confidence":0}],
            "edges":[{"from":"diagram","to":"failed","label":"extraction_failed"}],
            "explanation":f"VLM extraction failed: {reason[:200]}",
            "quiz":[{"q":"What happened?","options":["Extraction failed","Success","Cached","Demo"],"answer":0},
                    {"q":"What to do?","options":["Upload clearer image","Refresh","Wait","Nothing"],"answer":0},
                    {"q":"What is shown?","options":["Unknown - failed","Transformer","CNN","Blockchain"],"answer":0}],
            "diagram_type":"unknown"}

def extract_from_image(b64, ctx=None):
    last=""
    for attempt in range(1,MAX_RETRIES+1):
        if attempt>1: time.sleep(2**(attempt-2)+random.uniform(0,0.5))
        for model in VISION_MODELS:
            try:
                print(f"[VLM] {model} attempt {attempt}...")
                raw=_call(b64,ctx,model,last)
                parsed=_parse(raw)
                result=VLMResult(**parsed)
                contract={"nodes":[{"id":n.id,"label":n.label,"type":n.type,"confidence":n.confidence,"x":0,"y":0,"z":0} for n in result.nodes],
                          "edges":[{"from":e.from_node,"to":e.to_node,"label":e.label,"confidence":e.confidence} for e in result.edges],
                          "explanation":result.explanation,
                          "quiz":[{"q":q.q,"options":q.options,"answer":q.answer} for q in result.quiz],
                          "diagram_type":result.diagram_type}
                contract=clean_graph(contract)
                print(f"[VLM] OK {len(contract[\'nodes\'])} nodes {len(contract[\'edges\'])} edges via {model}")
                return contract
            except Exception as exc:
                last=str(exc); print(f"[VLM] {model} failed: {exc}")
    print("[VLM] All attempts failed. Using fallback.")
    return _fallback(last)

def extract_from_file(path, ctx=None):
    from pipeline.ocr import image_file_to_base64, pdf_page_to_base64
    ext=os.path.splitext(path)[1].lower()
    b64=pdf_page_to_base64(path) if ext==".pdf" else image_file_to_base64(path)
    return extract_from_image(b64,ctx)
'''.strip()

# ── 2. pipeline/graph.py ─────────────────────────────────────
files["pipeline/graph.py"] = '''
import networkx as nx

def build_graph(entities, relations):
    G=nx.DiGraph()
    for e in entities:
        G.add_node(e["id"],label=e.get("label",e["id"]),type=e.get("type","component"),confidence=float(e.get("confidence",1.0)))
    for r in relations:
        s,t=r.get("from"),r.get("to")
        if s and t and s in G and t in G and s!=t:
            G.add_edge(s,t,label=r.get("label","related_to"),confidence=float(r.get("confidence",1.0)))
    if G.number_of_edges()==0 and G.number_of_nodes()>0:
        print("[GRAPH] No edges found — VLM/LLM will infer semantic edges.")
    else:
        print(f"[GRAPH] {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G

def build_graph_from_contract(contract):
    return build_graph(contract.get("nodes",[]),contract.get("edges",[]))

def has_cycles(G):
    try: nx.find_cycle(G); return True
    except nx.NetworkXNoCycle: return False

def get_stats(G):
    return {"total_nodes":G.number_of_nodes(),"total_edges":G.number_of_edges(),
            "isolated_nodes":len(list(nx.isolates(G))),"has_cycles":has_cycles(G),
            "is_connected":nx.is_weakly_connected(G) if G.number_of_nodes()>0 else False}

def graph_to_dict(G):
    nodes=[{"id":n,"label":d.get("label",n),"type":d.get("type","component"),"confidence":d.get("confidence",1.0),"x":0.0,"y":0.0,"z":0.0} for n,d in G.nodes(data=True)]
    edges=[{"from":s,"to":t,"label":d.get("label",""),"confidence":d.get("confidence",1.0)} for s,t,d in G.edges(data=True)]
    return {"nodes":nodes,"edges":edges}
'''.strip()

# ── 3. pipeline/spatial.py ───────────────────────────────────
files["pipeline/spatial.py"] = '''
import math, re, random
import networkx as nx

COORD_SCALE=2.5
MIN_DIST=0.35

def map_spatial_coords(G):
    if G.number_of_nodes()==0: return G
    pos=nx.spring_layout(G,dim=3,seed=42,k=1.8)
    for nid,c in pos.items():
        G.nodes[nid]["x"]=round(float(c[0])*COORD_SCALE,3)
        G.nodes[nid]["y"]=round(float(c[1])*COORD_SCALE,3)
        G.nodes[nid]["z"]=round(float(c[2])*COORD_SCALE,3)
    return _resolve_overlaps(G)

def map_hierarchical_coords(G):
    if G.number_of_nodes()==0: return G
    try: order=list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        print("[SPATIAL] Cycle detected — falling back to spring layout")
        return map_spatial_coords(G)
    levels={}
    for n in order:
        p=list(G.predecessors(n))
        levels[n]=0 if not p else max(levels[x] for x in p)+1
    max_lv=max(levels.values()) if levels else 0
    by_level={}
    for n,lv in levels.items(): by_level.setdefault(lv,[]).append(n)
    for lv,nodes in by_level.items():
        cnt=len(nodes)
        for i,nid in enumerate(nodes):
            x=((i-(cnt-1)/2)/max(1,cnt-1))*COORD_SCALE*1.5 if cnt>1 else 0.0
            y=round(((lv/max_lv)*2-1)*COORD_SCALE,3) if max_lv>0 else 0.0
            random.seed(hash(nid)); z=round(random.uniform(-0.3,0.3),3)
            G.nodes[nid]["x"]=round(x,3); G.nodes[nid]["y"]=y; G.nodes[nid]["z"]=z; G.nodes[nid]["layout_level"]=lv
    return _resolve_overlaps(G)

def _resolve_overlaps(G,iterations=5):
    nodes=list(G.nodes())
    for _ in range(iterations):
        moved=False
        for i in range(len(nodes)):
            for j in range(i+1,len(nodes)):
                ni,nj=G.nodes[nodes[i]],G.nodes[nodes[j]]
                dx=ni.get("x",0.0)-nj.get("x",0.0); dy=ni.get("y",0.0)-nj.get("y",0.0)
                dist=math.sqrt(dx**2+dy**2) or 1e-6
                if dist<MIN_DIST:
                    push=(MIN_DIST-dist)/2+0.01; f=push/dist
                    ni["x"]=round(ni.get("x",0.0)+dx*f,3); ni["y"]=round(ni.get("y",0.0)+dy*f,3)
                    nj["x"]=round(nj.get("x",0.0)-dx*f,3); nj["y"]=round(nj.get("y",0.0)-dy*f,3)
                    moved=True
        if not moved: break
    return G

def _tokens(t):
    s={x for x in re.findall(r"[a-z0-9]+",str(t).lower()) if x not in {"a","an","the"}}
    if "normalization" in s: s.add("norm")
    return s

def map_diagram_coords(G,blocks):
    if not blocks: return G,0
    matched=0; used=set()
    for nid,data in G.nodes(data=True):
        nt=_tokens(data.get("label",nid))
        if not nt: continue
        best_i,best_s=None,0.0
        for idx,blk in enumerate(blocks):
            if idx in used: continue
            bt=_tokens(blk.get("text",""))
            ov=len(nt&bt)
            if not ov: continue
            sc=ov/len(nt)*2+ov/max(1,len(bt))
            if nt==bt: sc+=2
            if sc>best_s: best_i=idx; best_s=sc
        if best_i is None or best_s<2: continue
        blk=blocks[best_i]
        data["x"]=round((blk["left"]+blk["width"]/2)/blk["image_width"]-0.5)*4
        data["y"]=round((0.5-( blk["top"]+blk["height"]/2)/blk["image_height"])*4)
        data["z"]=round(float(data.get("z",0.0))*0.12,3)
        used.add(best_i); matched+=1
    return G,matched

def apply_layout(G,diagram_type="unknown",layout_blocks=None):
    layout_blocks=layout_blocks or []
    if diagram_type in ("hierarchical","flowchart"):
        print(f"[SPATIAL] {diagram_type} → hierarchical layout"); G=map_hierarchical_coords(G)
    else:
        print(f"[SPATIAL] {diagram_type} → spring layout"); G=map_spatial_coords(G)
    G,matched=map_diagram_coords(G,layout_blocks)
    if matched: print(f"[SPATIAL] {matched} OCR position overrides applied")
    return G,matched

def graph_to_contract_nodes(G):
    return [{"id":n,"label":d.get("label",n),"type":d.get("type","component"),"confidence":d.get("confidence",1.0),"x":d.get("x",0.0),"y":d.get("y",0.0),"z":d.get("z",0.0)} for n,d in G.nodes(data=True)]

def graph_to_contract_edges(G):
    return [{"from":s,"to":t,"label":d.get("label",""),"confidence":d.get("confidence",1.0)} for s,t,d in G.edges(data=True)]
'''.strip()

# ── 4. main.py ───────────────────────────────────────────────
files["main.py"] = '''
import json, os, sys
from pipeline.graph import build_graph, build_graph_from_contract, has_cycles, get_stats
from pipeline.graph_cleaner import clean_graph
from pipeline.ocr import extract_with_layout, pdf_has_text_layer
from pipeline.spatial import apply_layout, graph_to_contract_nodes, graph_to_contract_edges

def _is_image(p): return os.path.splitext(p)[1].lower() in {".png",".jpg",".jpeg",".bmp",".tiff"}
def _is_pdf(p): return os.path.splitext(p)[1].lower()==".pdf"

def _run_vlm_path(path):
    from pipeline.vlm import extract_from_file
    print("Step 1/3 — VLM extraction (image → knowledge graph)")
    contract=extract_from_file(path)
    print(f"           OK {len(contract.get(\'nodes\',[]))} nodes, {len(contract.get(\'edges\',[]))} edges\\n")
    diagram_type=contract.get("diagram_type","unknown")
    print("Step 2/3 — Graph construction + cycle check")
    G=build_graph_from_contract(contract)
    stats=get_stats(G)
    if stats["has_cycles"] and diagram_type in ("hierarchical","flowchart"):
        print("           WARNING: Cycles in hierarchical diagram — possible extraction error")
    print(f"           OK {stats}\\n")
    print(f"Step 3/3 — Spatial layout (type={diagram_type})")
    G,ocr_matches=apply_layout(G,diagram_type,[])
    print(f"           OK {ocr_matches} OCR overrides\\n")
    return clean_graph({"nodes":graph_to_contract_nodes(G),"edges":graph_to_contract_edges(G),
                        "explanation":contract.get("explanation",""),"quiz":contract.get("quiz",[]),
                        "diagram_type":diagram_type,"layout":"vlm","pipeline":"vlm"})

def _run_text_path(path):
    from pipeline.ner import extract as ner_extract
    from pipeline.llm import generate
    print("Step 1/4 — OCR extraction (text-layer PDF)")
    ocr=extract_with_layout(path); text=ocr["text"]; blocks=ocr.get("layout_blocks",[])
    print(f"           OK {len(text.split())} words\\n")
    print("Step 2/4 — NER entity + relation extraction")
    ner=ner_extract(text); entities=ner["entities"]; relations=ner["relations"]
    print(f"           OK {len(entities)} entities, {len(relations)} relations\\n")
    if len(entities)<2: raise ValueError("Not enough components detected. Upload a clearer diagram.")
    print("Step 3/4 — LLM semantic enrichment (Groq)")
    llm=generate(entities,relations,ocr_text=text)
    print()
    print("Step 4/4 — Graph + spatial layout")
    G=build_graph(llm["nodes"],llm["edges"])
    G,matched=apply_layout(G,"unknown",blocks)
    print(f"           OK {get_stats(G)}, {matched} OCR overrides\\n")
    return clean_graph({"nodes":graph_to_contract_nodes(G),"edges":graph_to_contract_edges(G),
                        "explanation":llm.get("explanation",""),"quiz":llm.get("quiz",[]),
                        "diagram_type":"unknown","layout":"diagram" if matched>=2 else "graph","pipeline":"text"})

def run_pipeline(path):
    print(f"\\n{'='*50}\\n  ArchViz-XR Pipeline v3\\n  Input: {path}")
    if _is_image(path):
        print("  Route : VLM (image)"); print(f"{'='*50}\\n"); return _run_vlm_path(path)
    if _is_pdf(path):
        if pdf_has_text_layer(path):
            print("  Route : OCR → NER → LLM (text-layer PDF)"); print(f"{'='*50}\\n"); return _run_text_path(path)
        else:
            print("  Route : VLM (scanned PDF)"); print(f"{'='*50}\\n"); return _run_vlm_path(path)
    raise ValueError(f"Unsupported file type: {os.path.splitext(path)[1]}")

def save_contract(c,out="output/contract.json"):
    os.makedirs("output",exist_ok=True)
    with open(out,"w",encoding="utf-8") as f: json.dump(c,f,indent=2,ensure_ascii=False)
    print(f"Contract saved → {out}")

def print_summary(c):
    types={}
    for n in c["nodes"]: t=n.get("type","?"); types[t]=types.get(t,0)+1
    print(f"\\n{'='*50}\\n  Pipeline: {c.get(\'pipeline\',\'?\')}  Type: {c.get(\'diagram_type\',\'?\')}\\n  Nodes: {len(c[\'nodes\'])}  Edges: {len(c[\'edges\'])}\\n{'='*50}\\n")

if __name__=="__main__":
    if len(sys.argv)<2: print("Usage: python main.py <image_or_pdf>"); sys.exit(1)
    p=sys.argv[1]
    if not os.path.exists(p): print(f"File not found: {p}"); sys.exit(1)
    c=run_pipeline(p); save_contract(c); print_summary(c)
'''.strip()

# ── 5. backend/adaptive/adaptive_engine.py ───────────────────
files["backend/adaptive/adaptive_engine.py"] = '''
from __future__ import annotations
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class QuizAttempt:
    question: str; topic: str; correct: bool; round_n: int

@dataclass
class LearnerSession:
    session_id: str
    attempts: list[QuizAttempt] = field(default_factory=list)
    round_number: int = 0

    def overall_score(self):
        if not self.attempts: return 50.0
        return 100.0*sum(1 for a in self.attempts if a.correct)/len(self.attempts)

    def recent_score(self,last_n=5):
        r=self.attempts[-last_n:] if len(self.attempts)>=last_n else self.attempts
        if not r: return 50.0
        return 100.0*sum(1 for a in r if a.correct)/len(r)

    def weak_topics(self,threshold=0.5):
        ts=defaultdict(list)
        for a in self.attempts:
            if a.topic: ts[a.topic].append(a.correct)
        weak=[(t,sum(v)/len(v)) for t,v in ts.items() if len(v)>=2 and sum(v)/len(v)<threshold]
        return [t for t,_ in sorted(weak,key=lambda x:x[1])]

    def next_suggested_topic(self,all_topics):
        weak=self.weak_topics()
        if weak: return weak[0]
        attempted={a.topic for a in self.attempts}
        for t in all_topics:
            if t not in attempted: return t
        return all_topics[0] if all_topics else None

_store={}; _lock=threading.Lock()

def _get(sid):
    with _lock:
        if sid not in _store: _store[sid]=LearnerSession(session_id=sid)
        return _store[sid]

def record_quiz_result(session_id,question,topic,correct):
    s=_get(session_id)
    with _lock: s.attempts.append(QuizAttempt(question=question,topic=topic,correct=correct,round_n=s.round_number))

def end_round(session_id):
    s=_get(session_id)
    with _lock: s.round_number+=1

def get_learning_level(session_id,all_topics=None):
    s=_get(session_id); score=s.recent_score(5); weak=s.weak_topics(); topics=all_topics or []
    next_t=s.next_suggested_topic(topics)
    if score<40: level,diff,hints,hb="beginner","easy",True,3
    elif score<70: level,diff,hints,hb="intermediate","medium",False,1
    else: level,diff,hints,hb="advanced","hard",False,0
    return {"level":level,"difficulty":diff,"hints":hints,"hint_budget":hb,
            "next_topic":next_t or (topics[0] if topics else ""),"score":round(score,1),"weak_topics":weak[:3]}

def calculate_score(quiz,answers):
    if not quiz or len(answers)<len(quiz): return 0.0
    return round(100.0*sum(1 for i,q in enumerate(quiz) if answers[i]==q.get("answer",-1))/len(quiz),1)

def reset_session(session_id):
    with _lock: _store.pop(session_id,None)
'''.strip()

# ── 6. backend/service/tutor_engine.py ──────────────────────
files["backend/service/tutor_engine.py"] = '''
from __future__ import annotations
import os
from typing import Optional
from dotenv import load_dotenv
from groq import Groq
load_dotenv()

MODEL="llama-3.1-8b-instant"

_SYS="""You are an adaptive AI tutor explaining academic diagrams in AR.
Adjust depth: beginner=simple analogies, intermediate=proper terms, advanced=technical depth.
Max 80 words. Be conversational — student hears this via text-to-speech."""

def _prompt(question,node_label,level,contract,weak_topics):
    neighbours=[]
    for edge in contract.get("edges",[]):
        for node in contract.get("nodes",[]):
            if node["id"]==edge.get("from") and node["label"]==node_label:
                tgt=next((n["label"] for n in contract["nodes"] if n["id"]==edge.get("to")),edge.get("to",""))
                neighbours.append(f"{node_label} → {edge[\'label\']} → {tgt}")
            elif node["id"]==edge.get("to") and node["label"]==node_label:
                src=next((n["label"] for n in contract["nodes"] if n["id"]==edge.get("from")),edge.get("from",""))
                neighbours.append(f"{src} → {edge[\'label\']} → {node_label}")
    weak=f"Student struggles with: {\', \'.join(weak_topics[:2])}." if weak_topics else ""
    expl=contract.get("explanation","")[:300]
    return f"Level: {level}\\nNode: {node_label}\\nConnections: {\'; \'.join(neighbours) or \'none\'}\\nDiagram: {expl}\\n{weak}\\nQuestion: \\"{question}\\"\\nAnswer in max 80 words for {level} level."

def _fallback(node_label,level):
    t={"beginner":f"{node_label} is a key part of this diagram — like one step in a recipe.",
       "intermediate":f"{node_label} processes its inputs and passes results to the next stage.",
       "advanced":f"{node_label} transforms its input representations according to learned parameters."}
    return {"answer":t.get(level,t["intermediate"]),"difficulty":{"beginner":"easy","intermediate":"medium","advanced":"hard"}.get(level,"medium"),"next_topic":"","source":"fallback"}

def generate_tutor_response(question,node_label,level,contract=None,weak_topics=None):
    contract=contract or {}; weak_topics=weak_topics or []
    api_key=os.getenv("GROQ_API_KEY")
    if not api_key: return _fallback(node_label,level)
    try:
        client=Groq(api_key=api_key)
        r=client.chat.completions.create(model=MODEL,temperature=0.4,max_tokens=200,
            messages=[{"role":"system","content":_SYS},{"role":"user","content":_prompt(question,node_label,level,contract,weak_topics)}])
        answer=r.choices[0].message.content.strip()
    except Exception as exc:
        print(f"[TUTOR] API error: {exc}"); return _fallback(node_label,level)
    return {"answer":answer,"difficulty":{"beginner":"easy","intermediate":"medium","advanced":"hard"}.get(level,"medium"),
            "next_topic":weak_topics[0] if weak_topics else "","source":"llm"}
'''.strip()

# ── Write all files ───────────────────────────────────────────
for rel_path, content in files.items():
    abs_path = os.path.join(REPO, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  Written: {rel_path}")

print("\nAll 6 files written successfully!")
