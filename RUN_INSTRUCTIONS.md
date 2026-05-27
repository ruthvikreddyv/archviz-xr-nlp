# ArchViz-XR Run Instructions

Run the project with two terminals.

## 1. Backend

```powershell
cd c:\Users\rohit\archviz-xr-nlp
$env:TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"
.\venv\Scripts\python.exe -m uvicorn backend.server:app --reload --port 8000
```

Keep this terminal running.

Backend URL:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## 2. Figma UI Frontend

Open a second terminal:

```powershell
cd "c:\Users\rohit\archviz-xr-nlp\Futuristic UI_UX for ArchViz-XR"
npm.cmd run dev -- --host 127.0.0.1 --port 5175
```

Open:

```text
http://127.0.0.1:5175
```

Useful pages:

```text
http://127.0.0.1:5175/upload
http://127.0.0.1:5175/results
http://127.0.0.1:5175/graph-viewer
```

## 3. Direct AR / Three.js Viewer

The real 3D graph viewer is served by the backend:

```text
http://127.0.0.1:8000/ar/index.html
```

The Figma UI `/graph-viewer` page embeds this same viewer.

## First-Time Frontend Setup

If dependencies are missing:

```powershell
cd "c:\Users\rohit\archviz-xr-nlp\Futuristic UI_UX for ArchViz-XR"
npm.cmd install
```

## Notes

- Tesseract must be installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- If Groq is not configured, the pipeline still works using fallback graph generation.
- To enable Groq LLM enrichment, set `GROQ_API_KEY` before running the backend.
- If upload says `Failed to fetch`, restart the backend and check that it is running on port `8000`.
