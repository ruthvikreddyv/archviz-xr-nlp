from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.1-8b-instant"


def build_prompt(entities: list, relations: list) -> str:
    entity_labels = [e["label"] for e in entities]
    relation_strs = [
        f"{r['from']} --{r['label']}--> {r['to']}"
        for r in relations
    ]

    prompt = f"""You are an AI system that analyzes academic diagrams and returns structured JSON.

The following concepts were extracted from a diagram:
Concepts: {entity_labels}

Existing relationships (may be generic):
{chr(10).join(relation_strs) if relation_strs else "None detected"}

Your tasks:
1. Classify each concept into one of three types:
   - "component" → a structural part (encoder, decoder, layer, head)
   - "process"   → an action or operation (attention, normalization, softmax)
   - "data"      → information flowing through (token, embedding, vector, output)

2. Identify meaningful semantic relationships between concepts. Use specific verbs:
   feeds, uses, produces, normalizes, applies, generates, transforms, passes, computes, outputs

3. Write a clear 2-3 sentence explanation of what this diagram shows.

4. Generate exactly 3 quiz questions to test understanding.

Return ONLY this exact JSON structure, nothing else:
{{
  "nodes": [
    {{"id": "concept_id", "label": "Concept Label", "type": "component|process|data"}}
  ],
  "edges": [
    {{"from": "concept_id", "to": "concept_id", "label": "verb"}}
  ],
  "explanation": "2-3 sentence explanation.",
  "quiz": [
    {{
      "q": "Question?",
      "options": ["A", "B", "C", "D"],
      "answer": 0
    }}
  ]
}}

Rules:
- Use underscores in ids, e.g. "multi_head_attention"
- Only create edges between concepts that genuinely relate
- Every concept must appear in nodes
- answer is index 0-3 of the correct option
- Return ONLY the JSON. No markdown. No explanation."""

    return prompt


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
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw:\n{text}")


def generate(entities: list, relations: list) -> dict:
    if not entities:
        raise ValueError("No entities provided to LLM module")

    print(f"[LLM] Calling Groq ({MODEL}) with {len(entities)} concepts...")

    prompt = build_prompt(entities, relations)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a JSON-only API. You never write explanations or markdown. You only output valid JSON objects."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=2000
    )

    raw = response.choices[0].message.content
    result = parse_response(raw)

    # Validate required fields
    for field in ["nodes", "edges", "explanation", "quiz"]:
        if field not in result:
            raise ValueError(f"LLM response missing '{field}' field")

    if len(result["quiz"]) == 0:
        raise ValueError("LLM returned empty quiz")

    print(f"[LLM] ✓ {len(result['nodes'])} nodes, {len(result['edges'])} semantic edges")
    print(f"[LLM] ✓ Explanation + {len(result['quiz'])} quiz questions ready")

    return result


# ── Quick test ─────────────────────────────────────────────
if __name__ == "__main__":
    sample_entities = [
        {"id": "encoder",            "label": "Encoder",            "type": "component"},
        {"id": "decoder",            "label": "Decoder",            "type": "component"},
        {"id": "multi_head_attention","label": "Multi-Head Attention","type": "process"},
        {"id": "query",              "label": "Query",              "type": "data"},
        {"id": "key",                "label": "Key",                "type": "data"},
        {"id": "value",              "label": "Value",              "type": "data"},
        {"id": "softmax",            "label": "Softmax",            "type": "process"},
        {"id": "embeddings",         "label": "Embeddings",         "type": "data"},
    ]
    sample_relations = []

    result = generate(sample_entities, sample_relations)

    print("\n── Nodes with types ────────────────")
    for n in result["nodes"]:
        print(f"  [{n['type']:10s}] {n['label']}")

    print("\n── Semantic edges ──────────────────")
    for e in result["edges"]:
        print(f"  {e['from']:25s} --{e['label']}--> {e['to']}")

    print("\n── Explanation ─────────────────────")
    print(result["explanation"])

    print("\n── Quiz ────────────────────────────")
    for i, q in enumerate(result["quiz"]):
        print(f"\n  Q{i+1}: {q['q']}")
        for j, opt in enumerate(q["options"]):
            marker = "✓" if j == q["answer"] else " "
            print(f"    [{marker}] {opt}")