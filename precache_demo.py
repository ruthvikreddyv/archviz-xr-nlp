"""
precache_demo.py
Ru's demo safety net - run this ONCE before the hackathon presentation.

Saves a pre-processed version of the Transformer diagram so the live demo
never runs OCR or calls the LLM during the presentation.
Instant load = zero risk of failure on stage.

Run:
    python precache_demo.py transformer.jpeg
"""

import json
import os
import sys
from pathlib import Path

from main import run_pipeline

PROJECT_ROOT = Path(__file__).resolve().parent
CACHE_PATH = PROJECT_ROOT / "output" / "demo_cache.json"


def precache(image_path: str) -> None:
    print("\n-- Pre-caching demo diagram --------")
    print(f"   Input : {image_path}")
    print(f"   Output: {CACHE_PATH}")
    print("   This may take 10-15 seconds...\n")

    contract = run_pipeline(image_path)

    # Save to dedicated cache file - never overwrite this.
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)

    print(f"\nOK Demo cached -> {CACHE_PATH}")
    print(f"  Nodes     : {len(contract['nodes'])}")
    print(f"  Edges     : {len(contract['edges'])}")
    print(f"  Explanation: {contract['explanation'][:60]}...")
    print("\n  During presentation: load demo_cache.json directly.")
    print("  Never run OCR live on stage.")


def load_cache() -> dict:
    """
    Load pre-cached demo contract instantly.
    As calls this in the /demo endpoint - no OCR, no LLM, instant response.
    """
    if not os.path.exists(CACHE_PATH):
        raise FileNotFoundError(
            f"Demo cache not found at {CACHE_PATH}. "
            "Run: python precache_demo.py transformer.jpeg"
        )
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python precache_demo.py <image_path>")
        print("Example: python precache_demo.py transformer.jpeg")
        sys.exit(1)

    precache(sys.argv[1])
