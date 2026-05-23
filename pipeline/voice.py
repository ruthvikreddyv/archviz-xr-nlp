"""
pipeline/voice.py
Ru's voice Q&A logic — As wraps this into POST /voice-query

Given:
  - user's spoken question (text after Web Speech API)
  - active node id (which node user is looking at in AR)
  - full contract (nodes + edges)

Returns:
  - answer string (spoken back by TTS)
  - highlight_node id (node to pulse in AR scene)
"""

from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"


def build_context(active_node_id: str, contract: dict) -> str:
    """
    Build rich context from the knowledge graph around the active node.
    This is what makes answers diagram-specific, not generic.
    """
    # Find the active node
    active = next(
        (n for n in contract["nodes"] if n["id"] == active_node_id),
        None
    )

    if not active:
        # Fallback — use full node list
        all_labels = [n["label"] for n in contract["nodes"]]
        return f"Diagram concepts: {all_labels}"

    # Find neighbours (nodes connected to active node)
    neighbours = []
    for edge in contract["edges"]:
        if edge["from"] == active_node_id:
            target = next(
                (n for n in contract["nodes"] if n["id"] == edge["to"]), None
            )
            if target:
                neighbours.append(
                    f"{active['label']} --{edge['label']}--> {target['label']}"
                )
        elif edge["to"] == active_node_id:
            source = next(
                (n for n in contract["nodes"] if n["id"] == edge["from"]), None
            )
            if source:
                neighbours.append(
                    f"{source['label']} --{edge['label']}--> {active['label']}"
                )

    context = f"""
Active node: {active['label']} (type: {active['type']})
Connected to:
{chr(10).join(neighbours) if neighbours else 'No direct connections'}
Diagram explanation: {contract['explanation']}
""".strip()

    return context


def find_most_relevant_node(answer: str, contract: dict) -> str:
    """
    Find which node the answer talks about most —
    this node gets highlighted in the AR scene.
    """
    answer_lower = answer.lower()
    best_node = None
    best_score = 0

    for node in contract["nodes"]:
        label_words = node["label"].lower().split()
        score = sum(1 for word in label_words if word in answer_lower)
        if score > best_score:
            best_score = score
            best_node = node["id"]

    return best_node or contract["nodes"][0]["id"]


def answer_question(question: str, active_node_id: str, contract: dict) -> dict:
    """
    Main function — answers a voice question in context of the AR diagram.

    Args:
        question:       The user's spoken question (from Web Speech API)
        active_node_id: Which node they're currently viewing in AR
        contract:       The full contract.json dict

    Returns:
        {
            "answer":         "Plain English answer (1-2 sentences)",
            "highlight_node": "node_id to pulse in AR scene"
        }
    """
    if not question or not question.strip():
        return {
            "answer": "I didn't catch that. Please try asking again.",
            "highlight_node": active_node_id
        }

    context = build_context(active_node_id, contract)

    prompt = f"""You are an AR tutor explaining an academic diagram to a student.
The student is currently looking at a specific part of the diagram.

Context about what they're looking at:
{context}

Student's question: "{question}"

Answer in 1-2 clear sentences. Be specific to the diagram context.
Do not say "In this diagram" — just answer directly.
Keep it under 50 words so it can be spoken aloud naturally."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a concise AI tutor. Give short, clear answers under 50 words."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=150
    )

    answer = response.choices[0].message.content.strip()
    highlight_node = find_most_relevant_node(answer, contract)

    return {
        "answer": answer,
        "highlight_node": highlight_node
    }


# ── Quick test ─────────────────────────────────────────────
if __name__ == "__main__":
    # Load the real contract.json
    contract_path = "output/contract.json"

    if not os.path.exists(contract_path):
        print("Error: output/contract.json not found. Run main.py first.")
        exit(1)

    with open(contract_path, "r") as f:
        contract = json.load(f)

    print(f"Loaded contract: {len(contract['nodes'])} nodes\n")

    # Simulate 3 voice questions from different nodes
    test_questions = [
        ("encoder",            "What does the encoder do?"),
        ("multi_head_attention","How does multi-head attention work?"),
        ("positional_encoding", "Why do we need positional encoding?"),
    ]

    for node_id, question in test_questions:
        print(f"── Question ────────────────────────")
        print(f"  Node    : {node_id}")
        print(f"  Question: {question}")
        result = answer_question(question, node_id, contract)
        print(f"  Answer  : {result['answer']}")
        print(f"  Highlight→ {result['highlight_node']}")
        print()