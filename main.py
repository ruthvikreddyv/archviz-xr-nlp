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
    print(f"           OK {len(contract.get('nodes',[]))} nodes, {len(contract.get('edges',[]))} edges\n")
    diagram_type=contract.get("diagram_type","unknown")
    print("Step 2/3 — Graph construction + cycle check")
    G=build_graph_from_contract(contract)
    stats=get_stats(G)
    if stats["has_cycles"] and diagram_type in ("hierarchical","flowchart"):
        print("           WARNING: Cycles in hierarchical diagram — possible extraction error")
    print(f"           OK {stats}\n")
    print(f"Step 3/3 — Spatial layout (type={diagram_type})")
    G,ocr_matches=apply_layout(G,diagram_type,[])
    print(f"           OK {ocr_matches} OCR overrides\n")
    return clean_graph({"nodes":graph_to_contract_nodes(G),"edges":graph_to_contract_edges(G),
                        "explanation":contract.get("explanation",""),"quiz":contract.get("quiz",[]),
                        "diagram_type":diagram_type,"layout":"vlm","pipeline":"vlm"})

def _run_text_path(path):
    from pipeline.ner import extract as ner_extract
    from pipeline.llm import generate
    print("Step 1/4 — OCR extraction (text-layer PDF)")
    ocr=extract_with_layout(path); text=ocr["text"]; blocks=ocr.get("layout_blocks",[])
    print(f"           OK {len(text.split())} words\n")
    print("Step 2/4 — NER entity + relation extraction")
    ner=ner_extract(text); entities=ner["entities"]; relations=ner["relations"]
    print(f"           OK {len(entities)} entities, {len(relations)} relations\n")
    if len(entities)<2: raise ValueError("Not enough components detected. Upload a clearer diagram.")
    print("Step 3/4 — LLM semantic enrichment (Groq)")
    llm=generate(entities,relations,ocr_text=text)
    print()
    print("Step 4/4 — Graph + spatial layout")
    G=build_graph(llm["nodes"],llm["edges"])
    G,matched=apply_layout(G,"unknown",blocks)
    print(f"           OK {get_stats(G)}, {matched} OCR overrides\n")
    return clean_graph({"nodes":graph_to_contract_nodes(G),"edges":graph_to_contract_edges(G),
                        "explanation":llm.get("explanation",""),"quiz":llm.get("quiz",[]),
                        "diagram_type":"unknown","layout":"diagram" if matched>=2 else "graph","pipeline":"text"})

def run_pipeline(path):
    print(f"\n{'='*50}\n  ArchViz-XR Pipeline v3\n  Input: {path}")
    if _is_image(path):
        print("  Route : VLM (image)"); print(f"{'='*50}\n"); return _run_vlm_path(path)
    if _is_pdf(path):
        if pdf_has_text_layer(path):
            print("  Route : OCR → NER → LLM (text-layer PDF)"); print(f"{'='*50}\n"); return _run_text_path(path)
        else:
            print("  Route : VLM (scanned PDF)"); print(f"{'='*50}\n"); return _run_vlm_path(path)
    raise ValueError(f"Unsupported file type: {os.path.splitext(path)[1]}")

def save_contract(c,out="output/contract.json"):
    os.makedirs("output",exist_ok=True)
    with open(out,"w",encoding="utf-8") as f: json.dump(c,f,indent=2,ensure_ascii=False)
    print(f"Contract saved → {out}")

def print_summary(c):
    types={}
    for n in c["nodes"]: t=n.get("type","?"); types[t]=types.get(t,0)+1
    print(f"\n{'='*50}\n  Pipeline: {c.get('pipeline','?')}  Type: {c.get('diagram_type','?')}\n  Nodes: {len(c['nodes'])}  Edges: {len(c['edges'])}\n{'='*50}\n")

if __name__=="__main__":
    if len(sys.argv)<2: print("Usage: python main.py <image_or_pdf>"); sys.exit(1)
    p=sys.argv[1]
    if not os.path.exists(p): print(f"File not found: {p}"); sys.exit(1)
    c=run_pipeline(p); save_contract(c); print_summary(c)