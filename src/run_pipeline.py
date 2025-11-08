# src/run_pipeline.py
"""
Phase 1c — Minimal pipeline runner with central LLM profile
- Loads .env (if present)
- Resolves per-stage model choices from config/llm_profiles.yml
- Falls back to env/defaults if profile or loader is unavailable
- Exposes resolved models via env vars for agents to consume
"""

from __future__ import annotations

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
ROOT = Path(__file__).resolve().parents[1]  # src/ → repo root
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if load_dotenv:
    load_dotenv(dotenv_path=ROOT / ".env")

print("Repo root:", ROOT)
print("SRC added:", SRC)

# -------------------------------------------------------------------
# 2) Imports (pipeline + optional config loader)
# -------------------------------------------------------------------
from storygraph.state import StoryState
from storygraph.router import Pipeline

# Optional config loader (preferred)
_loader = None
try:
    from storygraph.config_loader import load_llm_profile  # type: ignore
    _loader = "config_loader"
except Exception:
    _loader = None

# -------------------------------------------------------------------
# 3) Resolve models from YAML profile (or env/defaults)
# -------------------------------------------------------------------
import typing as _t

def _has(var: str) -> str:
    v = os.getenv(var)
    return "set" if v and len(v) > 10 else "missing"

def _resolve_from_profile(profile_name: str) -> dict:
    """
    Returns a dict:
      {
        "planner": "vendor/model",
        "draft": "vendor/model",
        "fact": "vendor/model",
        "revision": "vendor/model",
        "params": { ... }  # optional per-profile params if you need them later
      }
    """
    # Preferred path: use provided loader (already returns processed data)
    if _loader == "config_loader":
        return load_llm_profile(profile_name)

    # Fallback: read YAML directly
    cfg_path = ROOT / "config" / "llm_profiles.yaml"
    if cfg_path.exists():
        try:
            import yaml  # type: ignore
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            prof = (data.get("profiles") or {}).get(profile_name) or {}
            return _coerce_profile(prof)
        except Exception as e:
            print(f"[WARN] Could not read YAML at {cfg_path}: {e}")

    # Final fallback: environment variables only (no hardcoded defaults)
    stages = ["planner", "draft", "fact", "revision"]
    result = {}
    for stage in stages:
        env_var = f"LLM_{stage.upper()}_MODEL"
        model = os.getenv(env_var)
        if not model:
            raise RuntimeError(f"No model configured for {stage}. Set {env_var} environment variable or configure YAML profile.")
        result[stage] = model
    result["params"] = {}
    return result

def _coerce_profile(prof: dict) -> dict:
    apply_all = (prof or {}).get("apply_to_all")
    stages = (prof or {}).get("stages") or {}
    
    def _extract_model(stage_name, stage_config):
        if isinstance(stage_config, dict) and "model" in stage_config:
            return stage_config["model"]
        elif isinstance(stage_config, str):
            return stage_config
        elif apply_all:
            return apply_all
        else:
            raise RuntimeError(f"No model configured for stage '{stage_name}' and no apply_to_all fallback")
    
    out = {
        "planner": _extract_model("planner", stages.get("planner")),
        "draft": _extract_model("draft", stages.get("draft")),
        "fact": _extract_model("fact", stages.get("fact")),
        "revision": _extract_model("revision", stages.get("revision")),
        "params": (prof or {}).get("params") or {},
    }
    return out

PROFILE_NAME = os.getenv("LLM_PROFILE", "default")
resolved = _resolve_from_profile(PROFILE_NAME)

print("\nModel configuration (profile:", PROFILE_NAME + "):")
print("  Planner:", resolved["planner"])
print("  Draft:", resolved["draft"])
print("  Fact:", resolved["fact"])
print("  Revision:", resolved["revision"])

# Note: You asked to avoid global params and attach per-model params elsewhere.
# We surface them here in case future agents consume stage-specific params.
# For now we only print (do not enforce), to avoid breaking current agents.
params = resolved.get("params") or {}
if params:
    print("\nProfile params (not enforced here; for future use):")
    for k, v in params.items():
        print(f"  {k}: {v}")

print("\nAPI keys:")
print("  OPENAI_API_KEY:", _has("OPENAI_API_KEY"))
print("  ANTHROPIC_API_KEY:", _has("ANTHROPIC_API_KEY"))

# -------------------------------------------------------------------
# 4) Initial StoryState
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
# Pass resolved model configuration to the pipeline
models = {
    "planner": resolved["planner"],
    "draft": resolved["draft"], 
    "fact": resolved["fact"],
    "revision": resolved["revision"]
}
state = pipe.run_minimal(state.premise, state.venue, models=models)

print("\nPipeline finished. Metrics:")
for k, v in state.metrics.items():
    print(f"{k}: {v}")

print("\nDraft V2 (first 400 chars):")
print((state.draft_v2_concat or "")[:400])

# -------------------------------------------------------------------
# 6) Persist JSON (Pydantic v2 preferred)
# -------------------------------------------------------------------
OUTPUT_JSON = ROOT / "story_output.json"

def _dump_state_json(s) -> str:
    if hasattr(s, "model_dump_json"):  # Pydantic v2
        return s.model_dump_json(indent=2, ensure_ascii=False)  # type: ignore[attr-defined]
    if hasattr(s, "json"):  # Pydantic v1
        return s.json(indent=2, ensure_ascii=False)
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
    def _fmt_venue(v: str) -> str:
        """Return a submission-guidelines safe venue label.

        Rules:
        - If empty, return empty.
        - If it already contains the phrase 'submission guidelines', leave unchanged (idempotent).
        - Otherwise append ' - submission guidelines compatible'.
        This helps avoid implying official publication while drafting.
        """
        v = (v or "").strip()
        if not v:
            return ""
        if "submission guidelines" in v.lower():
            return v
        return f"{v} - submission guidelines compatible"

    safe_venue = _fmt_venue(venue)
    lines.append(f"# {title}" + (f" — {safe_venue}" if safe_venue else ""))
    lines.append("")

    # Prefer outline beat order
    beats = []
    if getattr(s, "outline", None) and getattr(s.outline, "beats", None):
        beats = [b.id for b in s.outline.beats if getattr(b, "id", None)]
    else:
        beats = list((s.drafts or {}).keys())

    if not beats:
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
