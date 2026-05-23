"""
ArchViz-XR — NLP Pipeline v2
Phase 2: Semantic edges + node type classification from LLM

Run:
    python main.py <path_to_image_or_pdf>
"""

import json
import sys
import os
from pipeline.ocr import extract
from pipeline.ner import extract as ner_extract
from pipeline.graph import build_graph
from pipeline.spatial import map_spatial_coords
from pipeline.llm import generate


def run_pipeline(file_path: str) -> dict:

    print(f"\n{'='*45}")
    print(f"  ArchViz-XR NLP Pipeline v2")
    print(f"  Input: {file_path}")
    print(f"{'='*45}\n")

    # ── Step 1: OCR ──────────────────────────────
    print("Step 1/5 — OCR extraction")
    text = extract(file_path)
    print(f"           ✓ {len(text.split())} words extracted\n")

    # ── Step 2: NER ──────────────────────────────
    print("Step 2/5 — Entity + relation extraction")
    ner_result = ner_extract(text)
    entities = ner_result["entities"]
    relations = ner_result["relations"]
    print(f"           ✓ {len(entities)} entities, {len(relations)} relations\n")

    if not entities:
        raise ValueError("No entities found. Check image quality.")

    # ── Step 3: LLM — semantic enrichment ────────
    # Phase 2: LLM now returns nodes WITH types AND semantic edges
    print("Step 3/5 — LLM semantic enrichment (Groq)")
    llm_result = generate(entities, relations)
    print()

    # Use LLM-enriched nodes and edges
    llm_nodes = llm_result["nodes"]   # typed nodes from LLM
    llm_edges = llm_result["edges"]   # semantic edges from LLM

    # ── Step 4: Spatial mapping ───────────────────
    print("Step 4/5 — Building graph + mapping 3D coordinates")

    # Build graph from LLM's richer output
    import networkx as nx
    G = nx.DiGraph()

    for node in llm_nodes:
        node_id = node["id"].replace(" ", "_").lower()
        G.add_node(node_id, label=node["label"], type=node["type"])

    for edge in llm_edges:
        src = edge["from"].replace(" ", "_").lower()
        tgt = edge["to"].replace(" ", "_").lower()
        if src in G and tgt in G:
            G.add_edge(src, tgt, label=edge["label"])

    # If LLM gave no edges, fall back to proximity
    if G.number_of_edges() == 0:
        print("           [fallback] Using proximity edges")
        node_list = list(G.nodes())
        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                if abs(i - j) <= 2:
                    G.add_edge(node_list[i], node_list[j], label="related_to")

    # Assign 3D coordinates
    from pipeline.spatial import map_spatial_coords
    G = map_spatial_coords(G)

    # Build final nodes list with coordinates
    final_nodes = []
    for node_id, data in G.nodes(data=True):
        final_nodes.append({
            "id": node_id,
            "label": data.get("label", node_id),
            "type": data.get("type", "component"),
            "x": data.get("x", 0.0),
            "y": data.get("y", 0.0),
            "z": data.get("z", 0.0)
        })

    # Build final edges list
    final_edges = []
    for src, tgt, data in G.edges(data=True):
        final_edges.append({
            "from": src,
            "to": tgt,
            "label": data.get("label", "")
        })

    print(f"           ✓ {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")

    # ── Step 5: Summary ───────────────────────────
    print("Step 5/5 — Assembling contract")

    contract = {
        "nodes": final_nodes,
        "edges": final_edges,
        "explanation": llm_result["explanation"],
        "quiz": llm_result["quiz"]
    }

    print(f"           ✓ Contract ready\n")
    return contract


def save_contract(contract: dict, output_path: str = "output/contract.json"):
    os.makedirs("output", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)
    print(f"✓ Contract saved → {output_path}")


def print_summary(contract: dict):
    # Count node types
    types = {}
    for n in contract["nodes"]:
        t = n.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    print(f"\n{'='*45}")
    print(f"  Pipeline Complete — Summary")
    print(f"{'='*45}")
    print(f"  Nodes      : {len(contract['nodes'])}")
    for t, count in types.items():
        print(f"    [{t:10s}] {count}")
    print(f"  Edges      : {len(contract['edges'])}")
    print(f"  Explanation: {contract['explanation'][:80]}...")
    print(f"  Quiz Qs    : {len(contract['quiz'])}")
    print(f"{'='*45}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_image_or_pdf>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File not found — {file_path}")
        sys.exit(1)

    contract = run_pipeline(file_path)
    save_contract(contract)
    print_summary(contract)
    print("Hand output/contract.json to Ro and As.")