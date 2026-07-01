import spacy
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_sm")

# ── Pattern matcher ───────────────────────────────────────
matcher = Matcher(nlp.vocab)

# Only high-confidence verb patterns
VERB_PATTERNS = [
    # "X uses Y"
    [{"DEP": "nsubj"}, {"LEMMA": {"IN": ["use","apply","compute"]}}, {"DEP": "dobj"}],
    # "X feeds Y"
    [{"DEP": "nsubj"}, {"LEMMA": {"IN": ["feed","pass","send","forward"]}}, {"DEP": "dobj"}],
    # "X produces Y"
    [{"DEP": "nsubj"}, {"LEMMA": {"IN": ["produce","generate","output","create","yield"]}}, {"DEP": "dobj"}],
    # "X normalizes / transforms Y"
    [{"DEP": "nsubj"}, {"LEMMA": {"IN": ["normalize","transform","encode","decode","embed"]}}, {"DEP": "dobj"}],
    # "X processes Y"
    [{"DEP": "nsubj"}, {"LEMMA": {"IN": ["process","handle","take","accept"]}}, {"DEP": "dobj"}],
]

for i, pattern in enumerate(VERB_PATTERNS):
    matcher.add(f"REL_{i}", [pattern])

# Words to strip from entity IDs
STRIP_PREFIXES = {"the_", "a_", "an_", "this_", "these_", "those_"}


def clean_entity(text: str) -> str:
    """Normalize entity text."""
    return text.strip().lower()


def clean_id(raw_id: str) -> str:
    """
    Remove articles from entity IDs.
    'the_encoder' → 'encoder'
    'a_decoder'   → 'decoder'
    """
    for prefix in STRIP_PREFIXES:
        if raw_id.startswith(prefix):
            return raw_id[len(prefix):]
    return raw_id


def is_valid_entity(text: str) -> bool:
    """Filter out noise."""
    if len(text) < 3:
        return False
    if text.isdigit():
        return False
    if not any(c.isalpha() for c in text):
        return False
    if text in {"the", "a", "an", "this", "these", "those"}:
        return False

    # NEW — skip all-caps titles like "THE_TRANSFORMER_ARCHITECTURE"
    # These are diagram titles, not concept nodes
    if text.replace("_", "").isupper() and len(text.replace("_","")) > 8:
        return False

    # NEW — skip generic single words that add no meaning
    if text.lower() in {"architecture", "overview", "diagram",
                        "figure", "model", "system", "framework"}:
        return False

    return True


def extract_entities(doc) -> list:
    """
    Extract meaningful noun chunks as candidate nodes.
    Deduplicate by cleaned ID so 'encoder' and 'the encoder' merge.
    """
    seen_ids = set()
    entities = []

    for chunk in doc.noun_chunks:
        raw   = clean_entity(chunk.text)
        eid   = clean_id(raw.replace(" ", "_"))

        if is_valid_entity(eid) and eid not in seen_ids:
            seen_ids.add(eid)
            # Use clean label (strip leading article)
            label = chunk.text.strip()
            for art in ("The ", "A ", "An ", "the ", "a ", "an "):
                if label.startswith(art):
                    label = label[len(art):]
                    break
            entities.append({
                "id":    eid,
                "label": label,
                "type":  "component"
            })

    for ent in doc.ents:
        raw = clean_entity(ent.text)
        eid = clean_id(raw.replace(" ", "_"))
        if is_valid_entity(eid) and eid not in seen_ids:
            seen_ids.add(eid)
            entities.append({
                "id":    eid,
                "label": ent.text.strip(),
                "type":  "named_entity"
            })

    return entities


def extract_relations_dependency(doc, entity_ids: set) -> list:
    """
    Dependency-based extraction — subject → verb → object triples.
    Only works when OCR text has full sentences.
    """
    relations = []
    seen_pairs = set()

    for token in doc:
        if token.pos_ != "VERB":
            continue

        subjects = [c for c in token.children if c.dep_ in ("nsubj", "nsubjpass")]
        objects  = [c for c in token.children if c.dep_ in ("dobj", "attr")]

        for subj in subjects:
            for obj in objects:
                src = clean_id(clean_entity(subj.text).replace(" ", "_"))
                tgt = clean_id(clean_entity(obj.text).replace(" ", "_"))

                if (src in entity_ids and tgt in entity_ids
                        and src != tgt
                        and (src, tgt) not in seen_pairs):
                    seen_pairs.add((src, tgt))
                    relations.append({
                        "from":  src,
                        "to":    tgt,
                        "label": token.lemma_
                    })

    return relations


def extract_relations_patterns(doc, entity_ids: set) -> list:
    """
    Pattern-based extraction using SpaCy Matcher.
    Strict nsubj → VERB → dobj structure only.
    No cross-sentence matching.
    """
    relations = []
    seen_pairs = set()
    matches = matcher(doc)

    for _, start, end in matches:
        span   = doc[start:end]
        tokens = list(span)

        subj  = next((t for t in tokens if t.dep_ == "nsubj"), None)
        obj   = next((t for t in reversed(tokens) if t.dep_ == "dobj"), None)
        verb  = next((t for t in tokens if t.pos_ == "VERB"), None)

        if not (subj and obj and verb):
            continue

        src = clean_id(clean_entity(subj.text).replace(" ", "_"))
        tgt = clean_id(clean_entity(obj.text).replace(" ", "_"))

        if (src in entity_ids and tgt in entity_ids
                and src != tgt
                and (src, tgt) not in seen_pairs):
            seen_pairs.add((src, tgt))
            relations.append({
                "from":  src,
                "to":    tgt,
                "label": verb.lemma_
            })

    return relations


def deduplicate_and_limit(relations: list, max_per_source: int = 3) -> list:
    """
    Remove duplicate pairs and limit to max_per_source edges per node.
    Prevents explosion when OCR produces repetitive text.
    """
    seen_pairs   = set()
    source_count = {}
    result       = []

    for rel in relations:
        src  = rel["from"]
        tgt  = rel["to"]
        pair = (src, tgt)

        if pair in seen_pairs:
            continue
        if source_count.get(src, 0) >= max_per_source:
            continue

        seen_pairs.add(pair)
        source_count[src] = source_count.get(src, 0) + 1
        result.append(rel)

    return result


def extract(text: str) -> dict:
    """
    Main function — 2-stage extraction (dependency + pattern).
    Proximity matching removed — too noisy for diagram OCR text.
    Results are deduplicated and capped at 3 edges per source node.
    """
    if not text or not text.strip():
        raise ValueError("Empty text passed to NER module")

    print(f"[NER] Processing {len(text.split())} words...")
    doc = nlp(text)

    entities   = extract_entities(doc)
    entity_ids = {e["id"] for e in entities}

    rel_dep = extract_relations_dependency(doc, entity_ids)
    rel_pat = extract_relations_patterns(doc, entity_ids)

    combined = deduplicate_and_limit(rel_dep + rel_pat, max_per_source=3)

    print(f"[NER] Found {len(entities)} entities")
    print(f"[NER] Relations — dep:{len(rel_dep)} pattern:{len(rel_pat)} final:{len(combined)}")

    return {"entities": entities, "relations": combined}


# ── Quick test ────────────────────────────────────────────
if __name__ == "__main__":
    sample_text = """
    The Transformer model uses an encoder and a decoder.
    The encoder processes the input tokens and generates embeddings.
    The decoder uses attention to attend over encoder outputs.
    Multi-head attention allows the model to focus on different positions.
    The query, key, and value matrices are used in the attention mechanism.
    Feed-forward layers process the attention output.
    The softmax function produces probability distributions.
    Positional encoding adds position information to embeddings.
    """

    result = extract(sample_text)

    print("\n── Entities ────────────────────────")
    for e in result["entities"]:
        print(f"  [{e['type']:12s}] {e['id']}")

    print("\n── Relations ───────────────────────")
    for r in result["relations"]:
        print(f"  {r['from']:25s} --{r['label']}--> {r['to']}")

    print(f"\nTotal: {len(result['entities'])} entities, {len(result['relations'])} relations")