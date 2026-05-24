# INSIGHTS.md — ArchViz-XR

## What We Learned Building This System

This document records real problems encountered during development and how they were solved.
These insights are valuable for anyone extending this framework.

---

## Insight 1 — OCR Extracts Very Little from Small Diagram Images

**Problem:**
When we first ran Tesseract OCR on a small JPEG of the Transformer architecture,
it extracted only 10 words — far too little for meaningful NLP processing.

**Root Cause:**
Tesseract performs poorly on low-resolution images. Diagram text is often small,
colored, or overlaid on backgrounds, which confuses the OCR engine.

**Fix:**
We added an OpenCV pre-processing step before Tesseract:
1. Resize image to 2x if width < 1000px using `cv2.INTER_CUBIC` interpolation
2. Convert to grayscale to remove color noise
3. Apply `cv2.THRESH_OTSU` adaptive thresholding to sharpen text contrast
4. Denoise with `cv2.fastNlMeansDenoising`

**Result:** Word extraction improved from 10 words to 102 words on the same image.

**Lesson:** Always pre-process images before OCR. Never pass raw color images directly to Tesseract.

---

## Insight 2 — Gemini Free Tier Quota Is Effectively Zero

**Problem:**
After setting up the Gemini API with a free-tier key, every call returned:
`429 RESOURCE_EXHAUSTED — limit: 0`

Even after creating a new API key and a new project, the quota remained exhausted
because earlier failed attempts consumed the daily limit.

**Root Cause:**
Google's free tier for `gemini-2.0-flash` and `gemini-1.5-flash` has extremely
limited daily quotas (~50 requests/day) that reset at midnight Pacific Time.
Failed requests still count toward the quota.

**Fix:**
Switched entirely to **Groq** with the `llama-3.1-8b-instant` model:
- Free tier: 14,400 requests/day
- No credit card required
- Faster response time than Gemini free tier
- Compatible JSON output for our pipeline

**Result:** LLM step works reliably with zero quota issues.

**Lesson:** For hackathon development with rapid iteration, Groq is more practical
than Gemini free tier. Gemini can be reintroduced in production with a paid key.

---

## Insight 3 — SpaCy NER Finds Zero Relations from Diagram OCR Text

**Problem:**
Our NER module uses SpaCy dependency parsing to find subject-verb-object triples.
Despite extracting 23 entities, it consistently found 0 relations.

**Root Cause:**
OCR text from diagrams is not natural language. It consists of isolated labels
("Encoder", "Multi-Head Attention", "Add & Norm") with no verbs or sentence
structure. SpaCy's dependency parser requires full sentences to detect relations.

**Fix:**
We delegated relation extraction entirely to the LLM layer. Instead of passing
empty relations to Gemini/Groq, we pass the entity list and ask the LLM to:
1. Infer semantically meaningful relations from domain knowledge
2. Use specific verbs: feeds, uses, produces, normalizes, applies, transforms
3. Return typed nodes (component / process / data) simultaneously

**Result:** 14–18 semantic edges generated per diagram with meaningful labels,
replacing 0 edges from NER or 63 noisy proximity edges from the fallback method.

**Lesson:** For academic diagram text, LLM-based relation inference outperforms
statistical NLP methods. Reserve SpaCy for full natural language text (research paper abstracts).

---

## Insight 4 — Raw NER Entities Contain Significant Noise

**Problem:**
SpaCy's noun chunk extraction returned 23 entities from 102 words, but many
were noise: fragments, OCR artifacts, and non-meaningful phrases.

**Root Cause:**
OCR introduces spacing errors and fragment words. SpaCy's noun chunk detector
picks up everything including short, meaningless chunks.

**Fix:**
Two-stage filtering:
1. Rule-based filter in `ner.py`: minimum 3 characters, must contain letters, not purely numeric
2. LLM semantic filter: Groq consolidates 23 raw entities into 16 meaningful concepts,
   discarding noise and merging duplicates ("add" + "add norm" → "Add & Norm")

**Result:** Clean 16-node graph representing actual Transformer components.

**Lesson:** LLMs are excellent semantic filters. Use rule-based NLP for speed,
LLM for quality — combine both in a two-stage pipeline.

---

## Insight 5 — google-generativeai Package Was Deprecated Mid-Development

**Problem:**
After installing `google-generativeai` and writing the LLM module, we received:
`FutureWarning: All support for the google.generativeai package has ended.`

The package still worked but model names changed between SDK versions,
causing `404 NOT_FOUND` errors when using `gemini-1.5-flash`.

**Fix:**
Migrated to the new `google-genai` SDK:
```
pip uninstall google-generativeai
pip install google-genai
```
Updated import: `from google import genai`
Updated model name: `gemini-2.0-flash-lite`

**Final decision:** Switched to Groq entirely (see Insight 2), making
this SDK migration moot for the current implementation.

**Lesson:** Always check the official SDK documentation at the start of a project.
AI provider SDKs change rapidly — pin your package versions in `requirements.txt`.

---

## Insight 6 — FastAPI Requires python-multipart for File Uploads

**Problem:**
When starting the FastAPI server with the `/analyze` endpoint, it crashed:
`RuntimeError: Form data requires "python-multipart" to be installed`

This error appeared at startup, not at request time, because FastAPI validates
all route dependencies on initialization.

**Fix:**
```
pip install python-multipart
```

**Lesson:** FastAPI's file upload (`UploadFile`) depends on `python-multipart`
but does not install it automatically. Always include it in `requirements.txt`
when using file upload endpoints.

---

## Insight 7 — NetworkX spring_layout Produces Different Results Each Run

**Problem:**
Every pipeline run produced different x,y,z coordinates for the same diagram,
making the AR scene layout inconsistent between runs.

**Root Cause:**
NetworkX's `spring_layout` uses random initialization by default.

**Fix:**
Added `seed=42` parameter:
```python
pos = nx.spring_layout(G, dim=3, seed=42, k=1.8)
```

**Result:** Identical, reproducible 3D layouts across all runs for the same input.

**Lesson:** Always set random seeds in layout algorithms for reproducible demos.
`seed=42` is the convention. Critical for pre-caching demo content.

---
## Insight 8 — Pipeline Generalizes Across Diagram Domains

**Tested on 3 diagram types:**

| Diagram | OCR Words | Nodes | Edges | Result |
|---------|-----------|-------|-------|--------|
| Transformer (AI/ML) | 102 | 18 | 22 | ✅ Accurate |
| CNN (Neural Network) | 24 | 18 | 14 | ✅ Correct |
| Blockchain | 73 | 13 | 16 | ✅ Correct |

**Key finding:**
The LLM semantic enrichment step compensates for sparse OCR output.
Even with only 3 OCR entities (CNN diagram), the LLM correctly
inferred 18 meaningful nodes about neural network architecture.
This confirms the core design decision: use NLP for speed,
LLM for accuracy and generalization.

**Minimum viable OCR threshold:**
- < 10 words → pipeline unreliable (LLM hallucinates)
- 10–30 words → LLM compensates well, output usable
- 30+ words → full pipeline performs optimally

## Summary Table

| # | Problem | Fix | Impact |
|---|---------|-----|--------|
| 1 | OCR extracts 10 words | OpenCV pre-processing | 10 → 102 words |
| 2 | Gemini quota = 0 | Switched to Groq | Unlimited dev calls |
| 3 | NER finds 0 relations | LLM relation inference | 0 → 14–18 semantic edges |
| 4 | 23 noisy NER entities | LLM semantic filtering | 23 → 16 clean nodes |
| 5 | SDK deprecated mid-build | Migrated to google-genai | No breaking changes |
| 6 | FastAPI crash on start | pip install python-multipart | Server starts cleanly |
| 7 | Different layout each run | seed=42 in spring_layout | Reproducible AR scenes |
