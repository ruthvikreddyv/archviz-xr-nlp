import spacy

# Load the English model (downloaded during setup)
nlp = spacy.load("en_core_web_sm")


def clean_entity(text: str) -> str:
    """
    Normalize entity text — lowercase, strip whitespace.
    'Encoder' and 'encoder' should be treated as the same thing.
    """
    return text.strip().lower()


def is_valid_entity(text: str) -> bool:
    """
    Filter out noise — short words, numbers, punctuation.
    We only want meaningful concept words.
    """
    if len(text) < 3:
        return False
    if text.isdigit():
        return False
    if not any(c.isalpha() for c in text):
        return False
    return True


def extract_entities(doc) -> list:
    """
    Extract meaningful concepts (noun chunks) from the text.
    These become the NODES in our knowledge graph.

    Example output:
    ["encoder", "decoder", "attention mechanism", "query", "key", "value"]
    """
    seen = set()
    entities = []

    for chunk in doc.noun_chunks:
        entity = clean_entity(chunk.text)
        if is_valid_entity(entity) and entity not in seen:
            seen.add(entity)
            entities.append({
                "id": entity.replace(" ", "_"),   # safe ID for graph
                "label": chunk.text.strip(),       # display name
                "type": "component"                # default type
            })

    # Also grab named entities SpaCy detects (ORG, PRODUCT, etc.)
    for ent in doc.ents:
        entity = clean_entity(ent.text)
        if is_valid_entity(entity) and entity not in seen:
            seen.add(entity)
            entities.append({
                "id": entity.replace(" ", "_"),
                "label": ent.text.strip(),
                "type": "named_entity"
            })

    return entities


def extract_relations(doc, entity_ids: set) -> list:
    """
    Extract how concepts connect to each other.
    These become the EDGES in our knowledge graph.

    Looks for patterns like:
    "encoder feeds decoder"  →  encoder --feeds--> decoder
    "attention uses query"   →  attention --uses--> query

    Example output:
    [{"from": "encoder", "to": "decoder", "label": "feeds"}]
    """
    relations = []
    seen_pairs = set()

    for token in doc:
        # Look for verb tokens that connect two noun concepts
        if token.pos_ == "VERB":
            subjects = [
                child for child in token.children
                if child.dep_ in ("nsubj", "nsubjpass")
            ]
            objects = [
                child for child in token.children
                if child.dep_ in ("dobj", "pobj", "attr")
            ]

            for subj in subjects:
                for obj in objects:
                    src = clean_entity(subj.text).replace(" ", "_")
                    tgt = clean_entity(obj.text).replace(" ", "_")
                    pair = (src, tgt)

                    # Only add relation if both ends are known entities
                    # and we haven't seen this pair before
                    if (src in entity_ids and
                        tgt in entity_ids and
                        pair not in seen_pairs):

                        seen_pairs.add(pair)
                        relations.append({
                            "from": src,
                            "to": tgt,
                            "label": token.lemma_  # base form of verb
                        })

    return relations


def extract(text: str) -> dict:
    """
    Main function — takes raw text, returns entities and relations.
    This is what the rest of the pipeline calls.

    Returns:
    {
        "entities": [...],   → nodes for the graph
        "relations": [...]   → edges for the graph
    }
    """
    if not text or not text.strip():
        raise ValueError("Empty text passed to NER module")

    print(f"[NER] Processing {len(text.split())} words...")

    doc = nlp(text)

    entities = extract_entities(doc)
    entity_ids = {e["id"] for e in entities}
    relations = extract_relations(doc, entity_ids)

    print(f"[NER] Found {len(entities)} entities, {len(relations)} relations")

    return {
        "entities": entities,
        "relations": relations
    }


# ── Quick test ──────────────────────────────────────────────
if __name__ == "__main__":
    # Test with a sample paragraph about the Transformer architecture
    sample_text = """
    The Transformer model uses an encoder and a decoder.
    The encoder processes the input tokens and generates embeddings.
    The decoder uses attention to attend over encoder outputs.
    Multi-head attention allows the model to focus on different positions.
    The query, key, and value matrices are used in the attention mechanism.
    Feed-forward layers process the attention output.
    The softmax function produces probability distributions.
    """

    result = extract(sample_text)

    print("\n── Entities (Nodes) ────────────────")
    for e in result["entities"]:
        print(f"  {e['id']:30s} | {e['label']}")

    print("\n── Relations (Edges) ───────────────")
    for r in result["relations"]:
        print(f"  {r['from']:20s} --{r['label']}--> {r['to']}")

    print(f"\nTotal: {len(result['entities'])} nodes, {len(result['relations'])} edges")