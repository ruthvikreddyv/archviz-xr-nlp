# ArchViz-XR

**Adaptive Research Comprehension via Hybrid NLP-XR Visualization**

> Upload any academic diagram. Watch it become an interactive 3D AR experience — automatically.

ArchViz-XR converts static research paper diagrams into intelligent, immersive AR visualizations using NLP, LLMs, and WebXR. No manual content authoring. Fully automatic.

Built for VISIONARY Hackathon 2.0 · Theme: Education + Open Innovation

---

## What It Does

1. **Upload** a diagram image (Transformer architecture, neural network, blockchain flow, anatomy chart)
2. **OCR** extracts all text from the diagram
3. **NLP** identifies concepts and relationships
4. **LLM** classifies nodes, infers semantic edges, generates explanation and quiz
5. **3D spatial mapping** assigns x,y,z coordinates to every node
6. **AR viewer** renders an animated, interactive 3D scene in the browser
7. **Voice Q&A** — ask questions about any node, get context-aware answers
8. **Adaptive quiz** — test understanding, difficulty adjusts to performance

---

## Team

| Person | Role |
|--------|------|
| Ru | NLP + AI pipeline lead |
| Ro | AR / XR visualization lead |
| As | Backend + adaptive engine lead |
| Ba | UI + integration + documentation lead |

---

## Project Structure

```
archviz-xr-nlp/           ← Python backend (Ru + As)
├── pipeline/
│   ├── ocr.py            → image/PDF → raw text
│   ├── ner.py            → text → entities + relations
│   ├── graph.py          → entities → NetworkX graph
│   ├── llm.py            → graph → semantic enrichment (Groq)
│   ├── spatial.py        → graph → 3D coordinates
│   └── voice.py          → question + context → AR answer
├── output/
│   ├── contract.json     → pipeline output (shared with frontend)
│   └── demo_cache.json   → pre-cached demo (load instantly)
├── main.py               → full pipeline runner
├── backend/server.py     → FastAPI backend
├── precache_demo.py      → pre-cache demo diagram
└── .env                  → API keys (never commit)

archviz-frontend/         ← React frontend (Ba + Ro)
├── src/
│   ├── App.jsx
│   └── components/
│       ├── UploadScreen.jsx
│       ├── PipelineScreen.jsx
│       └── ResultScreen.jsx
```

---

## Setup — Backend (Python)

### Requirements
- Python 3.11+
- Tesseract OCR 5.x

### Step 1 — Install Tesseract (Windows)
Download from: https://github.com/UB-Mannheim/tesseract/wiki
Install to: `C:\Program Files\Tesseract-OCR\`
Add to Windows PATH.

### Step 2 — Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### Step 3 — Install dependencies
```bash
pip install spacy pytesseract opencv-python pillow
pip install pymupdf networkx transformers
pip install google-genai pydantic fastapi uvicorn
pip install pytest python-dotenv groq python-multipart
python -m spacy download en_core_web_sm
```

### Step 4 — Configure API key
Create a `.env` file:
```
GROQ_API_KEY=your_groq_key_here
```
Get a free Groq key at: https://console.groq.com

### Step 5 — Pre-cache the demo
```bash
python precache_demo.py transformer.jpeg
```

### Step 6 — Start the backend
```bash
uvicorn backend.server:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## Setup — Frontend (React)

### Requirements
- Node.js 18+

### Install and run
```bash
cd archviz-frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## Running the Full Pipeline

### Analyze any diagram
```bash
python main.py your_diagram.png
```

Output: `output/contract.json`

### Run pipeline on a research paper PDF
```bash
python main.py paper.pdf
```

### Test voice Q&A
```bash
python pipeline/voice.py
```

---

## JSON Contract — API Reference

The pipeline produces a `contract.json` that all components consume:

```json
{
  "nodes": [
    {
      "id": "encoder",
      "label": "Encoder",
      "type": "component",
      "x": -0.47,
      "y": 0.959,
      "z": 0.621
    }
  ],
  "edges": [
    {
      "from": "encoder",
      "to": "contextual_representations",
      "label": "produces"
    }
  ],
  "explanation": "2-3 sentence plain English explanation",
  "quiz": [
    {
      "q": "Question text?",
      "options": ["A", "B", "C", "D"],
      "answer": 0
    }
  ]
}
```

### Node types
| Type | Color in AR | Meaning |
|------|-------------|---------|
| `component` | Purple | Structural parts (encoder, decoder, layer) |
| `process` | Amber | Operations (attention, normalization, softmax) |
| `data` | Gray | Information flow (tokens, embeddings, vectors) |

### Edge labels
Semantic verbs: `feeds`, `uses`, `produces`, `normalizes`, `applies`, `generates`, `transforms`, `computes`, `outputs`

---

## API Endpoints

### GET /demo
Load pre-cached Transformer demo instantly. No processing.
```
curl http://localhost:8000/demo
```

### POST /analyze
Run full pipeline on an uploaded diagram.
```
curl -X POST http://localhost:8000/analyze \
  -F "file=@transformer.jpeg"
```

### POST /voice-query
Answer a question in context of the active AR node.
```json
{
  "question": "What does the encoder do?",
  "active_node_id": "encoder",
  "contract": { ... }
}
```

### GET /health
Check server status.
```
curl http://localhost:8000/health
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| OCR | Tesseract 5 + OpenCV |
| NLP | SpaCy 3 (en_core_web_sm) |
| LLM | Groq API (LLaMA 3.1 8B) |
| Graph | NetworkX |
| 3D layout | NetworkX spring_layout (dim=3) |
| Backend | FastAPI + Uvicorn |
| Database | MongoDB |
| AR renderer | Three.js + WebXR |
| Frontend | React + Vite |

---

## Research Contribution

**Core innovation:** Semantic-to-Spatial Knowledge Transformation

Current AR educational systems require hand-authored 3D content.
ArchViz-XR eliminates this entirely — any diagram becomes an AR experience automatically.

The pipeline contribution: `image → OCR → NER → LLM enrichment → knowledge graph → 3D spatial layout → AR scene`

This addresses a documented gap in adaptive AR education research:
existing systems are static, domain-specific, and non-intelligent.

### Potential publications
- "An Adaptive AR Framework for Interactive Research Paper Understanding"
- "Semantic-to-Spatial Visualization using NLP and Augmented Reality"
- "Immersive Explainable AI Education using XR and Large Language Models"

---

## License

MIT License — open for research and educational use.
