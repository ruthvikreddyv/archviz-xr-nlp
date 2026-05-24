"""
ArchViz-XR FastAPI backend.

Run from the project root:
    uvicorn backend.server:app --reload --port 8000
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ==============================
# OPTIONAL IMPORTS
# ==============================

try:
    from pipeline.voice import answer_question
except Exception:
    answer_question = None

try:
    from backend.service.graph_cleaner import clean_graph
except Exception:

    def clean_graph(contract: dict) -> dict:
        replacements = {
            "multi-head_add": "Multi-Head Attention",
            "norm": "Normalization",
            "self-attention": "Self Attention",
        }

        for node in contract.get("nodes", []):
            label = node.get("label", "")
            replacement = replacements.get(label.lower())
            if replacement:
                node["label"] = replacement

        return contract


try:
    from backend.service.tutor_engine import generate_tutor_response
except Exception:

    def generate_tutor_response(question: str, level: str) -> dict:
        return {
            "answer": f"Adaptive tutor response for: {question}",
            "difficulty": level,
            "next_topic": "Self Attention",
        }


# ==============================
# FASTAPI APP
# ==============================

app = FastAPI(title="ArchViz-XR API", version="2.0")

# ==============================
# PATHS / CONFIG
# ==============================

CONTRACT_PATH = PROJECT_ROOT / "output" / "contract.json"
AR_VIEWER_DIR = PROJECT_ROOT / "archviz-ro"
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/jpg",
    "application/pdf",
}
ALLOWED_EXTENSIONS = {".jpeg", ".jpg", ".png", ".pdf"}

# ==============================
# CORS
# ==============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# MOUNT FRONTEND
# ==============================

if AR_VIEWER_DIR.is_dir():
    app.mount(
        "/ar",
        StaticFiles(directory=str(AR_VIEWER_DIR), html=True),
        name="ar-viewer",
    )

# ==============================
# HELPER FUNCTIONS
# ==============================


def save_latest_contract(contract: dict) -> None:
    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTRACT_PATH, "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)


def read_latest_contract() -> dict[str, Any]:
    if not CONTRACT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No contract found yet. Run /demo or POST /analyze first.",
        )

    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_upload(file: UploadFile) -> str:
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension: {suffix or 'missing'}",
        )

    return suffix


def load_demo_cache() -> dict[str, Any]:
    try:
        from precache_demo import load_cache
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load demo cache helper: {exc}",
        ) from exc

    try:
        return load_cache()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Demo cache not found. Run: python precache_demo.py transformer.jpeg",
        ) from exc


def analyze_file(file_path: str) -> dict[str, Any]:
    try:
        from main import run_pipeline
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load analysis pipeline: {exc}",
        ) from exc

    return run_pipeline(file_path)


# ==============================
# ROOT / HEALTH
# ==============================


@app.get("/")
def root() -> dict:
    return {
        "name": "ArchViz-XR API",
        "version": "2.0",
        "status": "running",
        "docs": "http://localhost:8000/docs",
        "endpoints": [
            "/demo",
            "/analyze",
            "/contract",
            "/voice-query",
            "/health",
            "/graph-summary",
            "/ar",
        ],
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": "2.0",
    }


# ==============================
# CONTRACT ENDPOINTS
# ==============================


@app.get("/demo")
def get_demo() -> dict:
    contract = load_demo_cache()
    contract = clean_graph(contract)
    save_latest_contract(contract)

    return {
        "status": "success",
        "source": "demo_cache",
        "contract": contract,
    }


@app.get("/contract")
def get_contract() -> dict[str, Any]:
    return read_latest_contract()


@app.get("/graph-summary")
def graph_summary() -> dict:
    contract = read_latest_contract()
    return {
        "nodes": len(contract.get("nodes", [])),
        "edges": len(contract.get("edges", [])),
        "quiz_questions": len(contract.get("quiz", [])),
        "has_explanation": bool(contract.get("explanation")),
    }


# ==============================
# ANALYZE ENDPOINT
# ==============================


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    suffix = validate_upload(file)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        contract = analyze_file(tmp_path)
        contract = clean_graph(contract)
        save_latest_contract(contract)

        return {
            "status": "success",
            "filename": file.filename,
            "contract": contract,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {exc}",
        ) from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ==============================
# VOICE QUERY
# ==============================


class VoiceQuery(BaseModel):
    question: str
    active_node_id: str
    contract: dict


@app.post("/voice-query")
def voice_query(body: VoiceQuery) -> dict:
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        level = "beginner"
        tutor_response = generate_tutor_response(
            question=body.question,
            level=level,
        )

        ai_response = None
        if answer_question:
            try:
                ai_response = answer_question(
                    question=body.question,
                    active_node_id=body.active_node_id,
                    contract=body.contract,
                )
            except Exception:
                ai_response = None

        answer = None
        highlight_node = body.active_node_id

        if isinstance(ai_response, dict):
            answer = ai_response.get("answer")
            highlight_node = ai_response.get("highlight_node") or highlight_node

        if not answer:
            answer = tutor_response.get("answer", "I could not generate an answer.")

        return {
            "status": "success",
            "question": body.question,
            "active_node": body.active_node_id,
            "answer": answer,
            "highlight_node": highlight_node,
            "adaptive_response": tutor_response,
            "ai_response": ai_response,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
