# src/run_pipeline.py
"""
Phase 1b — Minimal pipeline runner
This file replaces the Jupyter notebook so Andrew can convert it
into .ipynb later without repeating cell-by-cell code.
"""

import os
import sys
import json
from pathlib import Path

# -------------------------------------------------------------------
# 0) Load .env if present (repo root)
# -------------------------------------------------------------------
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

# -------------------------------------------------------------------
# 1) Ensure repo root/src is importable
# -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]      # src/ → repo root
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if load_dotenv:
    load_dotenv(dotenv_path=ROOT / ".env")

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
PLANNER_MODEL  = os.getenv("PLANNER_MODEL",  "openai/gpt-5")
DRAFT_MODEL    = os.getenv("DRAFT_MODEL",    "anthropic/claude-opus-4-1-20250805")
FACT_MODEL     = os.getenv("FACT_MODEL",     "openai/gpt-5")
REVISION_MODEL = os.getenv("REVISION_MODEL", "anthropic/claude-sonnet-4-5-20250929")

print("\nModel configuration:")
print("  Planner:", PLANNER_MODEL)
print("  Draft:", DRAFT_MODEL)
print("  Fact:", FACT_MODEL)
print("  Revision:", REVISION_MODEL)

# Just surface whether keys exist (don’t print secrets)
def _has(var: str) -> str:
    v = os.getenv(var)
    return "set" if v and len(v) > 10 else "missing"

print("\nAPI keys:")
print("  OPENAI_API_KEY:", _has("OPENAI_API_KEY"))
print("  ANTHROPIC_API_KEY:", _has("ANTHROPIC_API_KEY"))

# -------------------------------------------------------------------
# 4) Create initial StoryState
# -------------------------------------------------------------------
state = StoryState(
    premise=os.getenv("PREMISE", "A day in Kyiv during water outages"),
    venue=os.getenv("VENUE", "The Atlantic"),
    seed=int(os.getenv("SEED", "137")),
)

print("\nInitial StoryState:")
print(state)

# -------------------------------------------------------------------
# 5) Execute pipeline end-to-end
# -------------------------------------------------------------------
pipe = Pipeline(seed=state.seed)

print("\nRunning planner → draft → fact → revision ...")
# Pipeline.run_minimal currently reads agent defaults/environment internally.
# If/when Pipeline accepts model overrides, pass them explicitly here.
state = pipe.run_minimal(state.premise, state.venue)

print("\nPipeline finished. Metrics:")
for k, v in state.metrics.items():
    print(f"{k}: {v}")

print("\nDraft V2 (first 400 chars):")
print((state.draft_v2_concat or "")[:400])

# -------------------------------------------------------------------
# 6) Persist JSON (use Pydantic v2 method if available)
# -------------------------------------------------------------------
OUTPUT_JSON = ROOT / "story_output.json"

def _dump_state_json(s) -> str:
    # Prefer Pydantic v2 API; fall back to v1
    if hasattr(s, "model_dump_json"):
        return s.model_dump_json(indent=2, ensure_ascii=False)  # type: ignore[attr-defined]
    if hasattr(s, "json"):
        return s.json(indent=2, ensure_ascii=False)             # pydantic v1
    # Last resort: try dict()
    if hasattr(s, "dict"):
        return json.dumps(s.dict(), indent=2, ensure_ascii=False)
    raise RuntimeError("Cannot serialize StoryState")

OUTPUT_JSON.write_text(_dump_state_json(state), encoding="utf-8")
print(f"\nSaved story output to: {OUTPUT_JSON}")

# -------------------------------------------------------------------
# 7) Export Markdown with beat headers
# -------------------------------------------------------------------
EXPORTS_DIR = ROOT / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_MD = EXPORTS_DIR / "story_v2.md"

def _mk_markdown(s: StoryState) -> str:
    lines = []
    title = (s.premise or "Story").strip()
    venue = (s.venue or "").strip()
    if venue:
        lines.append(f"# {title} — {venue}")
    else:
        lines.append(f"# {title}")
    lines.append("")

    # Outline beats in order (if available), otherwise iterate drafts dict order
    beats = []
    if getattr(s, "outline", None) and getattr(s.outline, "beats", None):
        beats = [b.id for b in s.outline.beats if getattr(b, "id", None)]
    else:
        beats = list((s.drafts or {}).keys())

    if not beats:
        # No beats metadata; fallback to full text
        lines.append(s.draft_v2_concat or "")
        return "\n".join(lines)

    for beat_id in beats:
        lines.append(f"### BEAT: {beat_id}")
        scene = (s.drafts or {}).get(beat_id)
        if scene and getattr(scene, "text", None):
            lines.append("")
            lines.append(scene.text.strip())
            lines.append("")
        else:
            # If no per-beat text is stored, fall back to V2 concat once
            lines.append("")
            lines.append("(no scene text recorded; see combined draft below)")
            lines.append("")

    if s.draft_v2_concat:
        lines.append("---")
        lines.append("### Combined Draft (V2)")
        lines.append("")
        lines.append(s.draft_v2_concat.strip())

    return "\n".join(lines)

OUTPUT_MD.write_text(_mk_markdown(state), encoding="utf-8")
print(f"Saved Markdown to: {OUTPUT_MD}")
