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
    if re.search(r"\b\d*[xX×]\d*\b|\bnx\b",lower): return True
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
    label=re.sub(r"\s+"," ",label).strip()
    label=label.strip(" \t\r\n{}[]()<>|~`'\"\",;:.!?@#$%^*\\")
    if not label or any(m in label for m in ("\ufffd","\u00c2")): return None
    if _is_merged_label(label): return None
    if not re.findall(r"[A-Za-z]",label): return None
    alpha=re.sub(r"[^a-zA-Z]","",label).lower()
    if len(alpha)<=2 and alpha not in SHORT_LABEL_ALLOWLIST: return None
    if label.count("(")!=label.count(")") or label.count("[")!=label.count("]"): return None
    if re.search(r"[^A-Za-z0-9\s&+/_().\-':]",label): return None
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