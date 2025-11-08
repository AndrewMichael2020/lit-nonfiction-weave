"""
Phase 1b — Minimal pipeline runner
This file replaces the Jupyter notebook so Andrew can convert it
into .ipynb later without repeating cell-by-cell code.
"""

import os
import sys
from pathlib import Path

# -------------------------------------------------------------------
# 1) Ensure repo root/src is importable
# -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]      # src/ → repo root
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

print("Repo root:", ROOT)
print("SRC added:", SRC)

# -------------------------------------------------------------------
# 2) Import storygraph components
# -------------------------------------------------------------------
from storygraph.state import StoryState
from storygraph.router import Pipeline


# -------------------------------------------------------------------
# 3) Pull model names from environment (Phase 1b uses real LLM)
# -------------------------------------------------------------------
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "openai/gpt-5")
DRAFT_MODEL = os.getenv("DRAFT_MODEL", "anthropic/claude-opus-4-1-20250805")
FACT_MODEL = os.getenv("FACT_MODEL", "openai/gpt-5")
REVISION_MODEL = os.getenv("REVISION_MODEL", "anthropic/claude-sonnet-4-5-20250929")

print("\nModel configuration:")
print("  Planner:", PLANNER_MODEL)
print("  Draft:", DRAFT_MODEL)
print("  Fact:", FACT_MODEL)
print("  Revision:", REVISION_MODEL)


# -------------------------------------------------------------------
# 4) Create initial StoryState
# -------------------------------------------------------------------
state = StoryState(
    premise="A day in Kyiv during water outages",
    venue="The Atlantic",
    seed=137
)

print("\nInitial StoryState:")
print(state)


# -------------------------------------------------------------------
# 5) Execute pipeline end-to-end
# -------------------------------------------------------------------
pipe = Pipeline(seed=137)

print("\nRunning planner → draft → fact → revision ...")
state = pipe.run_minimal(state.premise, state.venue)

print("\nPipeline finished. Metrics:")
for k, v in state.metrics.items():
    print(f"{k}: {v}")

print("\nDraft V2 (first 400 chars):")
print(state.draft_v2_concat[:400])

# Optional: persist result
OUTPUT = ROOT / "story_output.json"
with OUTPUT.open("w", encoding="utf-8") as f:
    f.write(state.json())

print(f"\nSaved story output to: {OUTPUT}")
