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