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
    e=f"PREVIOUS FAILED: {err}. Fix before returning.\n" if err else ""
    c=f"PDF text context:\n{ctx[:1200]}\n" if ctx else ""
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
                print(f"[VLM] OK {len(contract['nodes'])} nodes {len(contract['edges'])} edges via {model}")
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