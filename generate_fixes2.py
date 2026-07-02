import os
REPO = os.path.dirname(os.path.abspath(__file__))
files = {}

files["requirements.txt"] = """
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
pydantic==2.8.2
groq==0.11.0
python-dotenv==1.0.1
pytesseract==0.3.13
opencv-python==4.10.0.84
Pillow==10.4.0
PyMuPDF==1.24.9
numpy==1.26.4
spacy==3.7.6
networkx==3.3
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
requests==2.32.3
pytest==8.3.2
pytest-asyncio==0.23.8
httpx==0.27.0
""".strip()

files["pipeline/graph_cleaner.py"] = '''
import re, unicodedata

VALID_TYPES = {"component","process","data","named_entity"}

SHORT_LABEL_ALLOWLIST = {
    "add","cnn","rnn","gru","lstm","mlp","ffn","mha","vit","gan","vae",
    "dqn","ppo","a3c","sac","fc","bn","ln","pe","lm","kv","qkv",
    "api","tcp","udp","rpc","sql","jwt","cdn","dns","vpc","iam",
    "tx","utxo","pow","pos","ui","io","id","os","q","k","v","w","x","y","z",
}

KNOWN_LABELS = {
    "multi head attention":"Multi-Head Attention","multi head add":"Multi-Head Attention",
    "multihead attention":"Multi-Head Attention","self attention":"Self-Attention",
    "cross attention":"Cross-Attention","norm":"Normalization","layer norm":"Layer Normalization",
    "batch norm":"Batch Normalization","add norm":"Add & Norm","add and norm":"Add & Norm",
    "ffn":"Feed-Forward Network","feed forward":"Feed-Forward Network",
    "feed forward network":"Feed-Forward Network","pos enc":"Positional Encoding",
    "conv":"Convolution","maxpool":"Max Pooling","avgpool":"Average Pooling","relu":"ReLU",
    "api gw":"API Gateway","api gateway":"API Gateway","tx":"Transaction",
}

def make_id(text):
    return re.sub(r"[^a-z0-9]+","_",str(text).lower()).strip("_")

def _canonical_key(label):
    return re.sub(r"[^a-z0-9]+"," ",label.lower()).strip()

def _is_merged_label(label):
    words = re.findall(r"[A-Za-z0-9]+",label)
    if len(words)>6: return True
    lower = label.lower()
    if re.search(r"\\b\\d*[xX\u00d7]\\d*\\b|\\bnx\\b",lower): return True
    pairs=[("input","output"),("encoder","decoder"),("source","target"),("query","key")]
    for a,b in pairs:
        if a in lower and b in lower:
            try:
                ia=next(i for i,w in enumerate(words) if w.lower()==a)
                ib=next(i for i,w in enumerate(words) if w.lower()==b)
                if abs(ia-ib)<=4: return True
            except StopIteration: pass
    if len(words)>=4 and words[0].lower()==words[len(words)//2].lower(): return True
    return False

def clean_label(raw):
    label=unicodedata.normalize("NFKC",str(raw or ""))
    label=re.sub(r"\\s+"," ",label).strip()
    label=label.strip(" \\t\\r\\n{}[]()<>|~`\'\\"\\",;:.!?@#$%^*\\\\")
    if not label or any(m in label for m in ("\\ufffd","\\u00c2")): return None
    if _is_merged_label(label): return None
    if not re.findall(r"[A-Za-z]",label): return None
    alpha=re.sub(r"[^a-zA-Z]","",label).lower()
    if len(alpha)<=2 and alpha not in SHORT_LABEL_ALLOWLIST: return None
    if label.count("(")!=label.count(")") or label.count("[")!=label.count("]"): return None
    if re.search(r"[^A-Za-z0-9\\s&+/_().\\-\':]",label): return None
    return KNOWN_LABELS.get(_canonical_key(label),label)

def clean_graph(contract):
    cleaned=[]; id_map={}; seen_ids=set()
    for node in contract.get("nodes",[]):
        label=clean_label(node.get("label") or node.get("id"))
        if not label: continue
        old_id=str(node.get("id",""))
        node_id=make_id(old_id) or make_id(label)
        if not node_id: continue
        id_map[old_id]=node_id
        if node_id in seen_ids: continue
        seen_ids.add(node_id)
        n=dict(node); n["id"]=node_id; n["label"]=label
        if n.get("type") not in VALID_TYPES: n["type"]="component"
        if "confidence" not in n: n["confidence"]=1.0
        cleaned.append(n)
    edges=[]; seen_e=set()
    for edge in contract.get("edges",[]):
        s=id_map.get(str(edge.get("from",""))); t=id_map.get(str(edge.get("to","")))
        lbl=make_id(edge.get("label","related_to")) or "related_to"
        key=(s,t,lbl)
        if s and t and s!=t and key not in seen_e:
            seen_e.add(key)
            e={"from":s,"to":t,"label":lbl}
            if "confidence" in edge: e["confidence"]=float(edge["confidence"])
            edges.append(e)
    c=dict(contract); c["nodes"]=cleaned; c["edges"]=edges; return c
'''.strip()

files["pipeline/ner.py"] = '''
import re
from typing import Optional

_NLP = None

SHORT_ALLOWLIST = {
    "q","k","v","ffn","mha","mlp","cnn","rnn","gru","lstm",
    "gan","vae","vit","gpt","rl","dqn","ppo","fc","bn","ln","pe","lm",
}

ARTICLE_PREFIXES = ("The ","A ","An ","the ","a ","an ")
STRIP_ID_PREFIXES = {"the_","a_","an_"}

RELATION_VERBS = {
    "use":"uses","apply":"applies","compute":"computes","feed":"feeds",
    "pass":"passes","send":"sends","forward":"forwards","produce":"produces",
    "generate":"generates","output":"outputs","normalize":"normalizes",
    "transform":"transforms","encode":"encodes","decode":"decodes",
    "embed":"embeds","process":"processes","attend":"attends","map":"maps",
}

MAX_EDGES_PER_SOURCE = 10

def _load_model():
    global _NLP
    if _NLP: return _NLP
    import spacy
    for m in ("en_core_web_trf","en_core_web_sm"):
        try: _NLP=spacy.load(m); print(f"[NER] Loaded {m}"); return _NLP
        except OSError: continue
    raise RuntimeError("No spaCy model. Run: python -m spacy download en_core_web_sm")

def clean_id(raw):
    for p in STRIP_ID_PREFIXES:
        if raw.startswith(p): return raw[len(p):]
    return raw

def strip_article(label):
    for a in ARTICLE_PREFIXES:
        if label.startswith(a): return label[len(a):]
    return label

def is_valid_entity(text):
    if not text or not any(c.isalpha() for c in text): return False
    if text in {"the","a","an","this","these","those","of","and","or"}: return False
    if text.isdigit(): return False
    if len(text)<=2: return text.lower() in SHORT_ALLOWLIST
    return True

def extract_entities(doc):
    seen=set(); entities=[]
    for chunk in doc.noun_chunks:
        raw=chunk.text.strip().lower(); eid=clean_id(raw.replace(" ","_"))
        if not is_valid_entity(eid) or eid in seen: continue
        seen.add(eid)
        entities.append({"id":eid,"label":strip_article(chunk.text.strip()),"type":"component","confidence":0.80})
    for ent in doc.ents:
        raw=ent.text.strip().lower(); eid=clean_id(raw.replace(" ","_"))
        if not is_valid_entity(eid) or eid in seen: continue
        seen.add(eid)
        entities.append({"id":eid,"label":ent.text.strip(),"type":"named_entity","confidence":0.90})
    return entities

def extract_relations(doc, entity_ids):
    relations=[]; seen=set()
    for token in doc:
        if token.pos_!="VERB": continue
        subjects=[c for c in token.children if c.dep_ in ("nsubj","nsubjpass")]
        objects=[c for c in token.children if c.dep_ in ("dobj","attr","pobj")]
        for s in subjects:
            for o in objects:
                src=clean_id(s.text.strip().lower().replace(" ","_"))
                tgt=clean_id(o.text.strip().lower().replace(" ","_"))
                pair=(src,tgt)
                if src in entity_ids and tgt in entity_ids and src!=tgt and pair not in seen:
                    seen.add(pair)
                    verb=RELATION_VERBS.get(token.lemma_,token.lemma_)
                    relations.append({"from":src,"to":tgt,"label":verb,"confidence":0.85})
    return relations

def deduplicate_and_limit(relations, max_per_source=MAX_EDGES_PER_SOURCE):
    seen=set(); counts={}; result=[]
    for r in relations:
        s,t=r["from"],r["to"]; pair=(s,t)
        if pair in seen or counts.get(s,0)>=max_per_source: continue
        seen.add(pair); counts[s]=counts.get(s,0)+1; result.append(r)
    return result

def extract(text):
    if not text or not text.strip(): raise ValueError("Empty text passed to NER")
    nlp=_load_model()
    print(f"[NER] Processing {len(text.split())} words...")
    doc=nlp(text)
    entities=extract_entities(doc)
    entity_ids={e["id"] for e in entities}
    relations=deduplicate_and_limit(extract_relations(doc,entity_ids))
    print(f"[NER] {len(entities)} entities, {len(relations)} relations")
    return {"entities":entities,"relations":relations}
'''.strip()

files["pipeline/llm.py"] = '''
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
    rels=[f"{r[\'from\']} --{r[\'label\']}--> {r[\'to\']}" for r in relations[:MAX_EDGES]]
    ctx=f"\\nRaw OCR text:\\n{ocr_text[:1500]}\\n" if ocr_text else ""
    err=f"\\nPREVIOUS FAILED: {error_hint}\\nFix before returning.\\n" if error_hint else ""
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
            print(f"[LLM] OK {len(result[\'nodes\'])} nodes, {len(result[\'edges\'])} edges (attempt {attempt})")
            return result
        except Exception as exc:
            last=str(exc); print(f"[LLM] Attempt {attempt} failed: {exc}")
    print(f"[LLM] All attempts failed — using fallback")
    return fallback_result(ents,rels,last)
'''.strip()

files["pipeline/ocr.py"] = '''
import base64, os, shutil
from collections import defaultdict
import cv2, fitz, numpy as np, pytesseract
from PIL import Image

def configure_tesseract():
    candidates=[os.getenv("TESSERACT_CMD"),shutil.which("tesseract"),
                r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"]
    for c in candidates:
        if c and os.path.exists(c):
            pytesseract.pytesseract.tesseract_cmd=c; return c
    return None

def _resize_if_small(img):
    h,w=img.shape[:2]
    if w<1200:
        scale=max(2.0,1200/w); img=cv2.resize(img,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
    return img

def _deskew(gray):
    edges=cv2.Canny(gray,50,150,apertureSize=3)
    lines=cv2.HoughLines(edges,1,np.pi/180,threshold=100)
    if lines is None: return gray
    angles=[np.degrees(t)-90 for _,t in lines[:,0] if -10<np.degrees(t)-90<10]
    if not angles: return gray
    angle=float(np.median(angles))
    if abs(angle)<0.3: return gray
    h,w=gray.shape[:2]; M=cv2.getRotationMatrix2D((w/2,h/2),angle,1.0)
    return cv2.warpAffine(gray,M,(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)

def _channel_ocr_passes(img, psm):
    config=f"--psm {psm} --oem 3"; results=[]
    def _ocr(ch,label):
        raw=pytesseract.image_to_string(ch,config=config)
        words=[w for w in raw.split() if len(w)>=2]
        results.append((raw,len(words),label))
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY); gray=_deskew(gray)
    denoised=cv2.fastNlMeansDenoising(gray,h=10)
    _,otsu=cv2.threshold(denoised,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU); _ocr(otsu,"otsu")
    for ch_idx,ch_name in enumerate([2,1,0]):
        ch=img[:,:,ch_name]; _,ct=cv2.threshold(ch,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU); _ocr(ct,f"ch{ch_idx}")
    adaptive=cv2.adaptiveThreshold(denoised,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,15,3); _ocr(adaptive,"adaptive")
    clahe=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)); eq=clahe.apply(denoised)
    _,eq_t=cv2.threshold(eq,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU); _ocr(eq_t,"clahe")
    return results

def preprocess_and_ocr(path):
    img=cv2.imread(path)
    if img is None: raise FileNotFoundError(f"Cannot load image: {path}")
    img=_resize_if_small(img); h,w=img.shape[:2]; psm=11 if w>h else 6
    passes=_channel_ocr_passes(img,psm)
    best_text,best_count,best_label=max(passes,key=lambda t:t[1])
    print(f"[OCR] Best pass: {best_label} → {best_count} words")
    merged=[]; seen=set()
    for raw,count,_ in sorted(passes,key=lambda t:t[1],reverse=True):
        if count<max(best_count*0.4,2): continue
        for word in raw.split():
            wl=word.lower()
            if wl not in seen and len(word)>=2: seen.add(wl); merged.append(word)
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY); gray=_deskew(gray)
    denoised=cv2.fastNlMeansDenoising(gray,h=10)
    _,thresh=cv2.threshold(denoised,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return " ".join(merged), _extract_layout_blocks(thresh)

def _extract_layout_blocks(processed):
    config="--psm 11 --oem 3"; data=pytesseract.image_to_data(processed,output_type=pytesseract.Output.DICT,config=config)
    ih,iw=processed.shape[:2]; lines=defaultdict(list)
    for i,text in enumerate(data["text"]):
        text=text.strip()
        if not text or len(text)<2 or int(data["conf"][i])<20: continue
        key=(data["page_num"][i],data["block_num"][i],data["par_num"][i],data["line_num"][i])
        lines[key].append({"text":text,"left":data["left"][i],"top":data["top"][i],"width":data["width"][i],"height":data["height"][i],"image_width":iw,"image_height":ih,"conf":int(data["conf"][i])})
    blocks=[]
    for words in lines.values():
        l=min(w["left"] for w in words); t=min(w["top"] for w in words)
        r=max(w["left"]+w["width"] for w in words); b=max(w["top"]+w["height"] for w in words)
        blocks.append({"text":" ".join(w["text"] for w in words),"left":l,"top":t,"width":r-l,"height":b-t,"image_width":iw,"image_height":ih})
        blocks.extend(words)
    return blocks

def pdf_has_text_layer(path):
    doc=fitz.open(path); total=sum(len(p.get_text().strip()) for p in doc); doc.close(); return total>=20

def extract_from_pdf(path):
    if not os.path.exists(path): raise FileNotFoundError(f"PDF not found: {path}")
    doc=fitz.open(path); pages=[p.get_text().strip() for p in doc if p.get_text().strip()]; doc.close()
    return " ".join(pages)

def rasterize_pdf_page(path,page_num=0,dpi=200):
    doc=fitz.open(path); page=doc[page_num]; mat=fitz.Matrix(dpi/72,dpi/72)
    pix=page.get_pixmap(matrix=mat,colorspace=fitz.csRGB); data=pix.tobytes("png"); doc.close(); return data

def rasterize_pdf_page_as_cv2(path,page_num=0,dpi=200):
    return cv2.imdecode(np.frombuffer(rasterize_pdf_page(path,page_num,dpi),np.uint8),cv2.IMREAD_COLOR)

def pdf_page_to_base64(path,page_num=0,dpi=200):
    return base64.b64encode(rasterize_pdf_page(path,page_num,dpi)).decode()

def image_file_to_base64(path):
    with open(path,"rb") as f: return base64.b64encode(f.read()).decode()

def extract_with_layout(path):
    ext=os.path.splitext(path)[1].lower()
    if ext==".pdf":
        if pdf_has_text_layer(path):
            print("[OCR] Text-layer PDF"); return {"text":extract_from_pdf(path),"layout_blocks":[],"is_scanned":False}
        else:
            print("[OCR] Scanned PDF — rasterising for OCR")
            if not configure_tesseract(): raise ValueError("Tesseract required for scanned PDFs")
            img=rasterize_pdf_page_as_cv2(path,dpi=200)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png",delete=False) as tmp:
                cv2.imwrite(tmp.name,img); tmp_path=tmp.name
            try: text,blocks=preprocess_and_ocr(tmp_path)
            finally: os.unlink(tmp_path)
            return {"text":text,"layout_blocks":blocks,"is_scanned":True}
    elif ext in {".png",".jpg",".jpeg",".bmp",".tiff"}:
        if not configure_tesseract(): raise ValueError("Tesseract not found")
        print("[OCR] Image — multi-channel OCR")
        text,blocks=preprocess_and_ocr(path)
        return {"text":text,"layout_blocks":blocks,"is_scanned":False}
    else: raise ValueError(f"Unsupported: {ext}")

def extract(path):
    r=extract_with_layout(path); text=r["text"]
    if not text.strip(): raise ValueError("No text extracted")
    print(f"[OCR] {len(text.split())} words"); return text
'''.strip()

files["tests/test_pipeline.py"] = '''
import json, os, pytest, numpy as np

def make_entities(*labels):
    return [{"id":l.lower().replace(" ","_"),"label":l,"type":"component"} for l in labels]

def make_relations(pairs):
    return [{"from":a,"to":b,"label":"feeds"} for a,b in pairs]

class TestOCR:
    def test_clean_ocr_text(self):
        from pipeline.ocr import extract_with_layout
        assert callable(extract_with_layout)

    def test_pdf_has_text_layer_false(self,tmp_path):
        import fitz
        doc=fitz.open(); doc.new_page(); p=str(tmp_path/"e.pdf"); doc.save(p); doc.close()
        from pipeline.ocr import pdf_has_text_layer
        assert pdf_has_text_layer(p) is False

    def test_pdf_has_text_layer_true(self,tmp_path):
        import fitz
        doc=fitz.open(); page=doc.new_page(); page.insert_text((72,72),"Encoder Decoder Attention Multi-Head Feed Forward")
        p=str(tmp_path/"t.pdf"); doc.save(p); doc.close()
        from pipeline.ocr import pdf_has_text_layer
        assert pdf_has_text_layer(p) is True

    def test_rasterize_returns_png(self,tmp_path):
        import fitz
        doc=fitz.open(); doc.new_page(); p=str(tmp_path/"p.pdf"); doc.save(p); doc.close()
        from pipeline.ocr import rasterize_pdf_page
        data=rasterize_pdf_page(p,dpi=72)
        assert data[:4]==b"\\x89PNG"

class TestNER:
    def test_valid_entity_allows_allowlist(self):
        from pipeline.ner import is_valid_entity
        assert is_valid_entity("ffn")
        assert is_valid_entity("mha")
        assert is_valid_entity("gru")

    def test_valid_entity_rejects_digits(self):
        from pipeline.ner import is_valid_entity
        assert not is_valid_entity("123")

    def test_valid_entity_rejects_articles(self):
        from pipeline.ner import is_valid_entity
        assert not is_valid_entity("the")

    def test_max_edges_per_source_is_10(self):
        from pipeline.ner import deduplicate_and_limit, MAX_EDGES_PER_SOURCE
        assert MAX_EDGES_PER_SOURCE==10
        rels=[{"from":"enc","to":f"n{i}","label":"feeds"} for i in range(15)]
        r=deduplicate_and_limit(rels)
        from collections import Counter
        counts=Counter(x["from"] for x in r)
        assert counts["enc"]==10

    def test_extract_returns_keys(self):
        from pipeline.ner import extract
        r=extract("The encoder processes tokens. The decoder generates output embeddings.")
        assert "entities" in r and "relations" in r

    def test_extract_raises_on_empty(self):
        from pipeline.ner import extract
        with pytest.raises(ValueError): extract("   ")

class TestGraph:
    def test_no_proximity_fallback_when_edges_present(self):
        from pipeline.graph import build_graph
        G=build_graph(make_entities("Encoder","Decoder","Attention"),
                      [{"from":"encoder","to":"decoder","label":"feeds"}])
        assert G.number_of_edges()==1

    def test_empty_relations_gives_zero_edges(self):
        from pipeline.graph import build_graph
        G=build_graph(make_entities("A","B","C","D"),[])
        assert G.number_of_edges()==0

    def test_cycle_detection(self):
        from pipeline.graph import build_graph, has_cycles
        G=build_graph([{"id":"a","label":"A","type":"component"},{"id":"b","label":"B","type":"component"}],
                      [{"from":"a","to":"b","label":"f"},{"from":"b","to":"a","label":"f"}])
        assert has_cycles(G)

    def test_get_stats(self):
        from pipeline.graph import build_graph, get_stats
        G=build_graph(make_entities("A","B"),[{"from":"a","to":"b","label":"feeds"}])
        s=get_stats(G)
        assert s["total_edges"]==1

class TestGraphCleaner:
    def test_clean_label_merged_rejected(self):
        from pipeline.graph_cleaner import clean_label
        assert clean_label("Input Tokens Output Tokens Decoder Encoder") is None

    def test_clean_label_known_alias(self):
        from pipeline.graph_cleaner import clean_label
        assert clean_label("Norm")=="Normalization"

    def test_clean_label_noise_rejected(self):
        from pipeline.graph_cleaner import clean_label
        assert clean_label(") ~ Ge") is None

    def test_clean_graph_removes_dangling(self):
        from pipeline.graph_cleaner import clean_graph
        c={"nodes":[{"id":"enc","label":"Encoder","type":"component"},{"id":"bad","label":") ~ Ge","type":"component"}],
           "edges":[{"from":"enc","to":"bad","label":"feeds"}],"quiz":[]}
        cleaned=clean_graph(c)
        ids={n["id"] for n in cleaned["nodes"]}
        assert "bad" not in ids
        assert all(e["from"] in ids and e["to"] in ids for e in cleaned["edges"])

class TestSpatial:
    def test_spring_layout_in_range(self):
        from pipeline.graph import build_graph
        from pipeline.spatial import map_spatial_coords, graph_to_contract_nodes
        G=build_graph(make_entities("A","B","C"),make_relations([("a","b"),("b","c")]))
        G=map_spatial_coords(G)
        for n in graph_to_contract_nodes(G):
            assert -5<=n["x"]<=5 and -5<=n["y"]<=5

    def test_hierarchical_layout(self):
        from pipeline.graph import build_graph
        from pipeline.spatial import map_hierarchical_coords, graph_to_contract_nodes
        G=build_graph(make_entities("In","Enc","Dec","Out"),
                      make_relations([("in","enc"),("enc","dec"),("dec","out")]))
        G=map_hierarchical_coords(G)
        nodes=graph_to_contract_nodes(G)
        assert len(nodes)==4
        ys=[n["y"] for n in nodes]
        assert len(set(ys))>1

class TestLLM:
    def test_make_id(self):
        from pipeline.llm import make_id
        assert make_id("Multi-Head Attention")=="multi_head_attention"
        assert make_id("Add & Norm")=="add_norm"
        assert make_id("   ")=="concept"

    def test_is_supported_label_strict(self):
        from pipeline.llm import is_supported_label
        ents=[{"label":"Encoder"},{"label":"Decoder"}]
        assert is_supported_label("Encoder Stack",ents)
        assert not is_supported_label("Convolutional Feature Map",ents)

    def test_fallback_no_proximity_edges(self):
        from pipeline.llm import fallback_result
        r=fallback_result(make_entities("A","B","C","D"),[])
        assert r["edges"]==[]

    def test_generate_raises_on_empty(self):
        from pipeline.llm import generate
        with pytest.raises(ValueError): generate([],[])

class TestContractSchema:
    CONTRACT={"nodes":[{"id":"enc","label":"Encoder","type":"component","x":0.1,"y":0.5,"z":-0.3},
                       {"id":"dec","label":"Decoder","type":"component","x":-0.2,"y":-0.5,"z":0.1}],
              "edges":[{"from":"enc","to":"dec","label":"feeds"}],
              "explanation":"Encoder-decoder architecture.",
              "quiz":[{"q":"What does the encoder do?","options":["Encode","Decode","Attend","Norm"],"answer":0}]}

    def test_nodes_have_required_fields(self):
        for n in self.CONTRACT["nodes"]:
            for f in ["id","label","type","x","y","z"]: assert f in n

    def test_edges_reference_valid_nodes(self):
        ids={n["id"] for n in self.CONTRACT["nodes"]}
        for e in self.CONTRACT["edges"]:
            assert e["from"] in ids and e["to"] in ids

    def test_quiz_structure(self):
        for q in self.CONTRACT["quiz"]:
            assert len(q["options"])==4 and 0<=q["answer"]<=3

    def test_contract_serialisable(self):
        json.dumps(self.CONTRACT)
'''.strip()

for rel_path, content in files.items():
    abs_path = os.path.join(REPO, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  Written: {rel_path}")

print("\nAll remaining files written!")
