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