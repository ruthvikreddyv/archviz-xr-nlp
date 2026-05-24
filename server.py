"""
server.py — ArchViz-XR FastAPI backend
As will expand this. For now Ru/Ba runs this to connect the frontend.

Endpoints:
  GET  /demo          → loads demo_cache.json instantly
  POST /analyze       → runs full pipeline on uploaded image
  POST /voice-query   → answers a question in AR context

Run:
  uvicorn server:app --reload --port 8000
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os
import shutil
import tempfile

from main import run_pipeline
from precache_demo import load_cache
from pipeline.voice import answer_question

app = FastAPI(title="ArchViz-XR API", version="1.0")
CONTRACT_PATH = "output/contract.json"
AR_VIEWER_DIR = "archviz-ro"

# Allow React frontend (localhost:5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir(AR_VIEWER_DIR):
    app.mount("/ar", StaticFiles(directory=AR_VIEWER_DIR, html=True), name="ar-viewer")


def save_latest_contract(contract: dict) -> None:
    os.makedirs(os.path.dirname(CONTRACT_PATH), exist_ok=True)
    with open(CONTRACT_PATH, "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)


# ── GET /demo ─────────────────────────────────────────────
@app.get("/demo")
def get_demo():
    """
    Load pre-cached Transformer demo instantly.
    No OCR, no LLM — just reads demo_cache.json.
    This is what the frontend demo button calls.
    """
    try:
        contract = load_cache()
        save_latest_contract(contract)
        return contract
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Demo cache not found. Run: python precache_demo.py transformer.jpeg"
        )


@app.get("/contract")
def get_contract():
    """
    Return the most recent contract for the AR viewer.
    This is updated by /demo and /analyze.
    """
    if not os.path.exists(CONTRACT_PATH):
        raise HTTPException(
            status_code=404,
            detail="No contract found yet. Run /demo or /analyze first."
        )

    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── POST /analyze ─────────────────────────────────────────
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    Full pipeline — upload a diagram image or PDF.
    Runs OCR → NER → Graph → Spatial → LLM.
    Returns contract.json structure.
    """
    # Validate file type
    allowed = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use JPG, PNG, or PDF."
        )

    # Save upload to temp file
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        contract = run_pipeline(tmp_path)
        save_latest_contract(contract)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
    finally:
        # Always clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── POST /voice-query ─────────────────────────────────────
class VoiceQuery(BaseModel):
    question: str
    active_node_id: str
    contract: dict


@app.post("/voice-query")
def voice_query(body: VoiceQuery):
    """
    Answer a spoken question in the context of the active AR node.
    Returns answer text + which node to highlight in the AR scene.
    """
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = answer_question(
            question=body.question,
            active_node_id=body.active_node_id,
            contract=body.contract
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /health ───────────────────────────────────────────
@app.get("/health")
def health():
    """Quick check — is the server running?"""
    return {"status": "ok", "version": "1.0"}


# ── GET / ─────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "ArchViz-XR API",
        "endpoints": ["/demo", "/analyze", "/contract", "/voice-query", "/health", "/ar"],
        "docs": "http://localhost:8000/docs"
    }
