import networkx as nx
import math


def map_spatial_coords(G: nx.DiGraph) -> nx.DiGraph:
    """
    Assign x, y, z coordinates to every node.
    Uses NetworkX spring_layout in 3D — automatically positions
    connected nodes near each other, separated nodes further apart.

    Output range: roughly -2.0 to +2.0 on each axis
    This matches what Ro's Three.js scene expects.
    """
    if G.number_of_nodes() == 0:
        return G

    # spring_layout in 3D — seed=42 makes it reproducible
    # k controls spacing between nodes (higher = more spread out)
    pos = nx.spring_layout(G, dim=3, seed=42, k=1.8)

    for node_id, coords in pos.items():
        G.nodes[node_id]["x"] = round(float(coords[0]) * 2, 3)
        G.nodes[node_id]["y"] = round(float(coords[1]) * 2, 3)
        G.nodes[node_id]["z"] = round(float(coords[2]) * 2, 3)

    return G


def graph_to_contract_nodes(G: nx.DiGraph) -> list:
    """
    Extract nodes with full spatial data — ready for JSON contract.
    """
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({
            "id": node_id,
            "label": data.get("label", node_id),
            "type": data.get("type", "component"),
            "x": data.get("x", 0.0),
            "y": data.get("y", 0.0),
            "z": data.get("z", 0.0)
        })
    return nodes


def graph_to_contract_edges(G: nx.DiGraph) -> list:
    """
    Extract edges — ready for JSON contract.
    """
    edges = []
    for src, tgt, data in G.edges(data=True):
        edges.append({
            "from": src,
            "to": tgt,
            "label": data.get("label", "")
        })
    return edges


# ── Quick test ────────────────────────────────────────────
if __name__ == "__main__":
    from graph import build_graph

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
        {"from": "encoder",   "to": "decoder",    "label": "feeds"},
        {"from": "attention", "to": "query",      "label": "uses"},
        {"from": "attention", "to": "key",        "label": "uses"},
        {"from": "attention", "to": "value",      "label": "uses"},
        {"from": "encoder",   "to": "embeddings", "label": "produces"},
        {"from": "softmax",   "to": "attention",  "label": "normalizes"},
    ]

    G = build_graph(sample_entities, sample_relations)
    G = map_spatial_coords(G)

    nodes = graph_to_contract_nodes(G)
    edges = graph_to_contract_edges(G)

    print("\n── Nodes with 3D coordinates ───────")
    for n in nodes:
        print(f"  {n['id']:15s} x={n['x']:6.3f}  y={n['y']:6.3f}  z={n['z']:6.3f}")

    print("\n── Edges ───────────────────────────")
    for e in edges:
        print(f"  {e['from']:15s} --{e['label']}--> {e['to']}")