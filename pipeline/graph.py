import networkx as nx


def build_graph(entities: list, relations: list) -> nx.DiGraph:
    G = nx.DiGraph()

    # Add all nodes
    for entity in entities:
        G.add_node(entity["id"], label=entity["label"], type=entity["type"])

    # Add real relations if we have them
    for rel in relations:
        src, tgt = rel["from"], rel["to"]
        if src in G and tgt in G:
            G.add_edge(src, tgt, label=rel["label"])

    # If still no edges — connect nodes that share similar words
    # This is common when OCR text lacks full sentences
    if G.number_of_edges() == 0:
        print("[GRAPH] No relations found - building proximity edges")
        node_list = list(G.nodes())
        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                a = node_list[i]
                b = node_list[j]
                # Connect nodes that are adjacent in the entity list
                # (they appeared near each other in the diagram text)
                if abs(i - j) <= 3:
                    G.add_edge(a, b, label="related_to")

    return G


def graph_to_dict(G: nx.DiGraph) -> dict:
    """
    Convert NetworkX graph to plain Python dict.
    This is the intermediate format before spatial mapping.
    """
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({
            "id": node_id,
            "label": data.get("label", node_id),
            "type": data.get("type", "component"),
            # x, y, z will be added by spatial.py later
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
        })

    edges = []
    for src, tgt, data in G.edges(data=True):
        edges.append({
            "from": src,
            "to": tgt,
            "label": data.get("label", "")
        })

    return {"nodes": nodes, "edges": edges}


def get_stats(G: nx.DiGraph) -> dict:
    """Quick summary of what the graph contains."""
    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "isolated_nodes": len(list(nx.isolates(G))),
        "is_connected": nx.is_weakly_connected(G) if G.number_of_nodes() > 0 else False
    }


# ── Quick test ────────────────────────────────────────────
if __name__ == "__main__":
    # Simulate what NER would return
    sample_entities = [
        {"id": "encoder",    "label": "Encoder",    "type": "component"},
        {"id": "decoder",    "label": "Decoder",    "type": "component"},
        {"id": "attention",  "label": "Attention",  "type": "component"},
        {"id": "query",      "label": "Query",      "type": "component"},
        {"id": "key",        "label": "Key",        "type": "component"},
        {"id": "value",      "label": "Value",      "type": "component"},
        {"id": "softmax",    "label": "Softmax",    "type": "process"},
        {"id": "embeddings", "label": "Embeddings", "type": "data"},
    ]

    sample_relations = [
        {"from": "encoder",   "to": "decoder",   "label": "feeds"},
        {"from": "attention", "to": "query",     "label": "uses"},
        {"from": "attention", "to": "key",       "label": "uses"},
        {"from": "attention", "to": "value",     "label": "uses"},
        {"from": "encoder",   "to": "embeddings","label": "produces"},
        {"from": "softmax",   "to": "attention", "label": "normalizes"},
    ]

    G = build_graph(sample_entities, sample_relations)
    stats = get_stats(G)
    result = graph_to_dict(G)

    print("\n── Graph Stats ─────────────────────")
    for k, v in stats.items():
        print(f"  {k:20s}: {v}")

    print("\n── Nodes ───────────────────────────")
    for node in result["nodes"]:
        print(f"  {node['id']:20s} | type: {node['type']}")

    print("\n── Edges ───────────────────────────")
    for edge in result["edges"]:
        print(f"  {edge['from']:15s} --{edge['label']}--> {edge['to']}")
