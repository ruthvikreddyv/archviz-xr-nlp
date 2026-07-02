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