from __future__ import annotations
import os
from typing import Optional
from dotenv import load_dotenv
from groq import Groq
load_dotenv()

MODEL="llama-3.1-8b-instant"

_SYS="""You are an adaptive AI tutor explaining academic diagrams in AR.
Adjust depth: beginner=simple analogies, intermediate=proper terms, advanced=technical depth.
Max 80 words. Be conversational — student hears this via text-to-speech."""

def _prompt(question,node_label,level,contract,weak_topics):
    neighbours=[]
    for edge in contract.get("edges",[]):
        for node in contract.get("nodes",[]):
            if node["id"]==edge.get("from") and node["label"]==node_label:
                tgt=next((n["label"] for n in contract["nodes"] if n["id"]==edge.get("to")),edge.get("to",""))
                neighbours.append(f"{node_label} → {edge['label']} → {tgt}")
            elif node["id"]==edge.get("to") and node["label"]==node_label:
                src=next((n["label"] for n in contract["nodes"] if n["id"]==edge.get("from")),edge.get("from",""))
                neighbours.append(f"{src} → {edge['label']} → {node_label}")
    weak=f"Student struggles with: {', '.join(weak_topics[:2])}." if weak_topics else ""
    expl=contract.get("explanation","")[:300]
    return f"Level: {level}\nNode: {node_label}\nConnections: {'; '.join(neighbours) or 'none'}\nDiagram: {expl}\n{weak}\nQuestion: \"{question}\"\nAnswer in max 80 words for {level} level."

def _fallback(node_label,level):
    t={"beginner":f"{node_label} is a key part of this diagram — like one step in a recipe.",
       "intermediate":f"{node_label} processes its inputs and passes results to the next stage.",
       "advanced":f"{node_label} transforms its input representations according to learned parameters."}
    return {"answer":t.get(level,t["intermediate"]),"difficulty":{"beginner":"easy","intermediate":"medium","advanced":"hard"}.get(level,"medium"),"next_topic":"","source":"fallback"}

def generate_tutor_response(question,node_label,level,contract=None,weak_topics=None):
    contract=contract or {}; weak_topics=weak_topics or []
    api_key=os.getenv("GROQ_API_KEY")
    if not api_key: return _fallback(node_label,level)
    try:
        client=Groq(api_key=api_key)
        r=client.chat.completions.create(model=MODEL,temperature=0.4,max_tokens=200,
            messages=[{"role":"system","content":_SYS},{"role":"user","content":_prompt(question,node_label,level,contract,weak_topics)}])
        answer=r.choices[0].message.content.strip()
    except Exception as exc:
        print(f"[TUTOR] API error: {exc}"); return _fallback(node_label,level)
    return {"answer":answer,"difficulty":{"beginner":"easy","intermediate":"medium","advanced":"hard"}.get(level,"medium"),
            "next_topic":weak_topics[0] if weak_topics else "","source":"llm"}