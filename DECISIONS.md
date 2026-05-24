# DECISIONS.md — ArchViz-XR

## Architectural and Technology Decisions

This document explains every major technology choice made during development,
including what alternatives were considered and why we chose what we chose.
These justifications are intended for judges, researchers, and future developers.

---

## Decision 1 — Groq (LLaMA 3.1) over Gemini / OpenAI for LLM

**Chosen:** Groq API with `llama-3.1-8b-instant`

**Alternatives considered:**
- Google Gemini 1.5 Flash / 2.0 Flash Lite
- OpenAI GPT-3.5 / GPT-4o

**Why Groq:**

| Criteria | Groq (LLaMA) | Gemini Free | OpenAI |
|---|---|---|---|
| Daily free requests | 14,400 | ~50 | 0 (paid only) |
| Credit card required | No | No | Yes |
| Response speed | Very fast | Moderate | Fast |
| JSON reliability | High | High | High |
| Setup complexity | Low | Low | Low |

For a hackathon with rapid iteration cycles, Groq's generous free quota
is critical. Gemini's free tier was exhausted within minutes of development.
OpenAI requires billing setup which adds friction.

**Trade-off:** LLaMA 3.1 8B is smaller than GPT-4o. For complex multi-step
reasoning, GPT-4o would give richer outputs. For structured JSON generation
from concept lists, LLaMA 3.1 8B is sufficient and fast.

**Future:** Swap to Gemini Pro or GPT-4o with a paid key for production.

---

## Decision 2 — WebXR + Three.js over Unity + ARCore

**Chosen:** Three.js with WebXR for AR rendering

**Alternatives considered:**
- Unity + AR Foundation + ARCore (Android native)
- A-Frame (WebXR framework)
- 8th Wall (commercial WebAR)

**Why WebXR + Three.js:**

1. **Zero install for judges** — judges open a URL in Chrome. No APK download,
   no device pairing, no app store. This is critical for hackathon demos.

2. **Cross-platform** — works on Android Chrome, desktop Chrome, and as a
   3D orbit view on any browser without AR hardware.

3. **Development speed** — Three.js has no build pipeline complexity.
   A working 3D scene can be running in under an hour.

4. **JSON integration** — Three.js consumes our `contract.json` directly
   in JavaScript with no serialization layer needed.

**Trade-off:** Native Unity/ARCore gives better AR tracking, depth perception,
and performance on mobile. For a research prototype and hackathon demo,
browser-based AR is sufficient and dramatically lowers the barrier to entry.

**Future:** Unity + AR Foundation for v2 mobile app with persistent spatial anchors.

---

## Decision 3 — SpaCy over Pure HuggingFace for NER

**Chosen:** SpaCy `en_core_web_sm` for entity extraction

**Alternatives considered:**
- HuggingFace `dslim/bert-base-NER` transformer model
- NLTK
- Stanford CoreNLP

**Why SpaCy:**

1. **Speed** — SpaCy processes text in milliseconds. HuggingFace BERT-based NER
   takes 2–5 seconds per passage on CPU. For a real-time pipeline, speed matters.

2. **Lightweight** — `en_core_web_sm` is 12MB. BERT-NER models are 400MB+.
   Faster to install, lower memory footprint, better for deployment.

3. **Sufficient for our use case** — We use SpaCy for initial entity extraction,
   then pass results to the LLM for semantic enrichment. SpaCy doesn't need to
   be perfect — it just needs to identify candidate concepts.

4. **Dependency parsing** — SpaCy's dependency parser is excellent for
   subject-verb-object extraction, which no lightweight alternative matches.

**Trade-off:** BERT-based NER is more accurate on technical text. For diagram
labels ("Multi-Head Attention", "Positional Encoding"), BERT would recognize
these as technical entities more reliably than SpaCy's statistical model.

**Hybrid approach used:** SpaCy for speed + LLM for accuracy. Best of both.

---

## Decision 4 — NetworkX spring_layout for 3D Spatial Positioning

**Chosen:** NetworkX `spring_layout` with `dim=3`

**Alternatives considered:**
- Manual coordinate assignment
- D3.js force simulation (client-side)
- Graphviz hierarchical layout
- t-SNE dimensionality reduction

**Why NetworkX spring_layout:**

1. **Automatic** — no manual coordinate assignment needed. The algorithm
   positions connected nodes near each other and isolated nodes further apart.

2. **Semantically meaningful** — nodes that share many edges cluster together
   in 3D space, which maps naturally to conceptual proximity in the diagram.

3. **Reproducible** — with `seed=42`, every run produces identical coordinates
   for the same graph. Critical for demo pre-caching.

4. **In our existing stack** — NetworkX is already used for graph construction.
   No additional library needed.

**Trade-off:** For hierarchical diagrams (like the Transformer encoder-decoder stack),
a hierarchical layout (Sugiyama algorithm) would be more faithful to the original
diagram's visual structure. Spring layout may place the encoder and decoder
at arbitrary positions rather than top-bottom as in the original paper.

**Future:** Detect diagram type (hierarchical vs network) and apply the appropriate
layout algorithm automatically.

---

## Decision 5 — FastAPI over Flask for the Backend

**Chosen:** FastAPI with Uvicorn

**Alternatives considered:**
- Flask
- Django REST Framework
- Express.js (Node)

**Why FastAPI:**

1. **Automatic API documentation** — FastAPI generates interactive docs at `/docs`
   automatically from type hints. Our teammates can test all endpoints without
   reading any documentation.

2. **Pydantic validation** — request bodies are validated automatically.
   Malformed requests return clear error messages without any extra code.

3. **Async support** — FastAPI is built on Starlette/asyncio. File uploads
   and LLM calls can be handled asynchronously for better performance.

4. **Type safety** — Python type hints throughout prevent entire classes of bugs
   that would surface at runtime in Flask.

**Trade-off:** Flask is simpler for very small APIs. FastAPI has slightly more
boilerplate for basic routes. For a multi-endpoint API with file uploads and
complex request bodies, FastAPI's structure pays off.

---

## Decision 6 — MongoDB over SQL for Data Storage

**Chosen:** MongoDB (via As's implementation)

**Alternatives considered:**
- PostgreSQL
- SQLite
- Firebase Firestore

**Why MongoDB:**

1. **Schema flexibility** — our `contract.json` structure varies between diagrams
   (different numbers of nodes and edges). SQL requires fixed schemas; MongoDB
   stores arbitrary JSON natively.

2. **Direct JSON storage** — the pipeline output is already JSON. MongoDB stores
   it without any ORM mapping or serialization layer.

3. **Session data structure** — learner models, quiz attempts, and interaction
   logs are naturally document-shaped, not relational.

4. **Fast prototyping** — no migration files, no schema definitions. Insert a
   document and it works.

**Trade-off:** SQL with proper relations would be more efficient for querying
aggregated learning analytics (e.g., "which concepts do all users struggle with").
For the hackathon scope, MongoDB's flexibility outweighs this.

---

## Decision 7 — Vite + React over Next.js or plain HTML

**Chosen:** Vite + React for the frontend

**Alternatives considered:**
- Next.js
- Plain HTML + vanilla JavaScript
- Vue.js

**Why Vite + React:**

1. **Speed** — Vite's dev server starts in under 1 second. Hot module replacement
   means UI changes reflect instantly during development.

2. **Component model** — our 3-screen flow (Upload → Pipeline → Result) maps
   cleanly to React components with state management.

3. **Three.js integration** — React Three Fiber (R3F) provides a declarative
   React API for Three.js, making AR scene integration straightforward.

4. **Team familiarity** — React is the most widely known frontend framework,
   reducing onboarding friction for teammates.

**Trade-off:** Next.js would provide server-side rendering and better SEO.
For a hackathon demo running locally, neither is needed. Vite + React is
faster to set up and iterate on.

---

## Summary

| Component | Chosen | Key Reason |
|---|---|---|
| LLM | Groq / LLaMA 3.1 | 14,400 free requests/day |
| AR renderer | Three.js + WebXR | Browser-based, zero install |
| NLP | SpaCy + LLM hybrid | Speed + accuracy combined |
| 3D layout | NetworkX spring_layout | Semantic clustering, reproducible |
| Backend | FastAPI | Auto docs, type safety, async |
| Database | MongoDB | Flexible JSON schema |
| Frontend | Vite + React | Fast dev, component model |
