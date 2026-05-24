import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.1-8b-instant"
MAX_CONCEPTS = 18
MAX_EDGES = 24
VALID_TYPES = {"component", "process", "data", "named_entity"}


def make_id(text: str) -> str:
    node_id = re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")
    return node_id or "concept"


def guess_type(label: str, current_type: str = "component") -> str:
    if current_type in VALID_TYPES:
        return current_type

    text = label.lower()
    if any(word in text for word in ["token", "output", "input", "embedding", "sequence", "vector", "data"]):
        return "data"
    if any(word in text for word in ["attention", "norm", "add", "encoding", "softmax", "generate", "feed", "compute"]):
        return "process"
    return "component"


def fallback_result(entities: list, relations: list, reason: str = "") -> dict:
    nodes = []
    seen = set()

    for entity in entities[:MAX_CONCEPTS]:
        label = entity.get("label") or entity.get("id") or "Concept"
        node_id = make_id(entity.get("id") or label)
        if node_id in seen:
            continue
        seen.add(node_id)
        nodes.append({
            "id": node_id,
            "label": label,
            "type": guess_type(label, entity.get("type", "component")),
        })

    node_ids = {node["id"] for node in nodes}
    edges = []
    edge_seen = set()

    for relation in relations[:MAX_EDGES]:
        src = make_id(relation.get("from", ""))
        tgt = make_id(relation.get("to", ""))
        label = relation.get("label", "related_to")
        key = (src, tgt, label)
        if src == tgt or src not in node_ids or tgt not in node_ids or key in edge_seen:
            continue
        edge_seen.add(key)
        edges.append({"from": src, "to": tgt, "label": label})

    if not edges:
        for i in range(max(0, len(nodes) - 1)):
            edges.append({"from": nodes[i]["id"], "to": nodes[i + 1]["id"], "label": "related_to"})
            if len(edges) >= min(MAX_EDGES, 12):
                break

    explanation = "This diagram has been converted into a knowledge graph of extracted concepts and relationships."
    if reason:
        explanation += " A fallback summary was used because the LLM response was not valid JSON."

    return {
        "nodes": nodes,
        "edges": edges,
        "explanation": explanation,
        "quiz": [
            {
                "q": "What does each sphere in the AR view represent?",
                "options": ["A concept from the diagram", "A file upload", "A database row", "A camera"],
                "answer": 0,
            },
            {
                "q": "What do the lines between spheres represent?",
                "options": ["Visual style only", "Relationships between concepts", "Image pixels", "Quiz answers"],
                "answer": 1,
            },
            {
                "q": "Why is OCR used in this pipeline?",
                "options": ["To extract text from the uploaded diagram", "To render WebXR", "To start the server", "To install packages"],
                "answer": 0,
            },
        ],
    }


def build_prompt(entities: list, relations: list) -> str:
    entities = entities[:MAX_CONCEPTS]
    relations = relations[:MAX_EDGES]
    entity_labels = [e["label"] for e in entities]
    relation_strs = [f"{r['from']} --{r['label']}--> {r['to']}" for r in relations]

    return f"""You analyze academic diagrams and return structured JSON.

Concepts extracted from the diagram:
{json.dumps(entity_labels)}

Existing relationships:
{chr(10).join(relation_strs) if relation_strs else "None detected"}

Return exactly one JSON object with this shape:
{{
  "nodes": [
    {{"id": "concept_id", "label": "Concept Label", "type": "component"}}
  ],
  "edges": [
    {{"from": "concept_id", "to": "concept_id", "label": "uses"}}
  ],
  "explanation": "Two clear sentences about the diagram.",
  "quiz": [
    {{"q": "Question?", "options": ["A", "B", "C", "D"], "answer": 0}}
  ]
}}

Rules:
- Use only these node types: component, process, data, named_entity.
- Use underscore lowercase ids.
- Return at most {MAX_CONCEPTS} nodes and at most {MAX_EDGES} edges.
- Do not create repeated edges.
- Do not create self-loops where from and to are the same.
- Generate exactly 3 quiz questions.
- Return JSON only."""


def parse_response(response_text: str) -> dict:
    text = response_text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}")


def validate_result(result: dict, entities: list, relations: list) -> dict:
    for field in ["nodes", "edges", "explanation", "quiz"]:
        if field not in result:
            raise ValueError(f"LLM response missing '{field}' field")

    nodes = []
    seen_nodes = set()
    for node in result.get("nodes", [])[:MAX_CONCEPTS]:
        label = str(node.get("label") or node.get("id") or "Concept")
        node_id = make_id(node.get("id") or label)
        if node_id in seen_nodes:
            continue
        seen_nodes.add(node_id)
        nodes.append({
            "id": node_id,
            "label": label,
            "type": guess_type(label, node.get("type", "component")),
        })

    if not nodes:
        return fallback_result(entities, relations, "empty nodes")

    node_ids = {node["id"] for node in nodes}
    edges = []
    seen_edges = set()
    for edge in result.get("edges", []):
        src = make_id(edge.get("from", ""))
        tgt = make_id(edge.get("to", ""))
        label = str(edge.get("label") or "related_to")
        key = (src, tgt, label)
        if src == tgt or src not in node_ids or tgt not in node_ids or key in seen_edges:
            continue
        seen_edges.add(key)
        edges.append({"from": src, "to": tgt, "label": label})
        if len(edges) >= MAX_EDGES:
            break

    quiz = []
    for item in result.get("quiz", [])[:3]:
        options = item.get("options", [])
        answer = item.get("answer", 0)
        if isinstance(options, list) and len(options) == 4 and isinstance(answer, int) and 0 <= answer <= 3:
            quiz.append({
                "q": str(item.get("q") or "What does this diagram show?"),
                "options": [str(option) for option in options],
                "answer": answer,
            })

    fallback = fallback_result(entities, relations)
    while len(quiz) < 3:
        quiz.append(fallback["quiz"][len(quiz)])

    return {
        "nodes": nodes,
        "edges": edges or fallback["edges"],
        "explanation": str(result.get("explanation") or fallback["explanation"]),
        "quiz": quiz,
    }


def generate(entities: list, relations: list) -> dict:
    if not entities:
        raise ValueError("No entities provided to LLM module")

    limited_entities = entities[:MAX_CONCEPTS]
    limited_relations = relations[:MAX_EDGES]
    print(f"[LLM] Calling Groq ({MODEL}) with {len(limited_entities)} concepts...")

    prompt = build_prompt(limited_entities, limited_relations)
    messages = [
        {
            "role": "system",
            "content": "You are a JSON-only API. Return one valid JSON object. Never repeat edges. Never add markdown.",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
        except TypeError:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=4000,
            )
    except Exception as e:
        print(f"[LLM] Warning: Groq call failed: {e}")
        result = fallback_result(limited_entities, limited_relations, str(e))
        print(f"[LLM] OK: {len(result['nodes'])} nodes, {len(result['edges'])} fallback edges")
        print(f"[LLM] OK: fallback explanation + {len(result['quiz'])} quiz questions ready")
        return result

    raw = response.choices[0].message.content
    try:
        result = validate_result(parse_response(raw), limited_entities, limited_relations)
    except ValueError as e:
        print(f"[LLM] Warning: {e}")
        result = fallback_result(limited_entities, limited_relations, str(e))

    print(f"[LLM] OK: {len(result['nodes'])} nodes, {len(result['edges'])} semantic edges")
    print(f"[LLM] OK: explanation + {len(result['quiz'])} quiz questions ready")
    return result


if __name__ == "__main__":
    sample_entities = [
        {"id": "encoder", "label": "Encoder", "type": "component"},
        {"id": "decoder", "label": "Decoder", "type": "component"},
        {"id": "multi_head_attention", "label": "Multi-Head Attention", "type": "process"},
        {"id": "query", "label": "Query", "type": "data"},
    ]
    print(json.dumps(generate(sample_entities, []), indent=2))
