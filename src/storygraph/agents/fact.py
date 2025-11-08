from __future__ import annotations
import pathlib
from typing import Dict, List
from ..state import StoryState        # ✅ ClaimGraph removed
from ..llm import LLMClient, LLMConfig
from ..json_utils import coerce_json


# -----------------------------------------------------
# Load fact-checking prompt
# -----------------------------------------------------

ROOT = pathlib.Path(__file__).resolve().parents[3]
PROMPT = (ROOT / "src" / "prompts" / "fact.txt").read_text(encoding="utf-8")


def _split(prompt: str):
    sys = prompt.split("[system]\n", 1)[1].split("[output_schema]", 1)[0].strip()
    schema = prompt.split("[output_schema]\n", 1)[1].split("[user]", 1)[0].strip()
    user = prompt.split("[user]\n", 1)[1].strip()
    return sys, schema, user


# -----------------------------------------------------
# Run FactAgent — Phase 1b minimal viable implementation
# -----------------------------------------------------

def run(
    state: StoryState,
    model: str = None,
    sources_dir: str = "data/sources"
) -> StoryState:
    """
    Phase-1b FactAgent:

    ✓ collects local text files as quote evidence  
    ✓ sends each drafted scene to the LLM  
    ✓ expects JSON:
        {
          "scene_id": "...",
          "claims": [
            {
              "claim": "...",
              "substantiated": true/false,
              "evidence_ids": [...]
            }
          ]
        }
    ✓ aggregates into state.claim_graph
    """

    # -------------------------------------------------
    # 1) Gather source quotes
    # -------------------------------------------------
    quotes = []
    src_path = pathlib.Path(sources_dir)

    if src_path.exists():
        for fp in src_path.glob("*.txt"):
            quotes.append(
                {
                    "id": fp.stem,
                    "file": fp.name,
                    "quote": fp.read_text(encoding="utf-8")[:500],
                }
            )

    # -------------------------------------------------
    # 2) Prepare prompt
    # -------------------------------------------------
    system, output_schema, user_tmpl = _split(PROMPT)

    cfg = LLMConfig(model=model or "openai/gpt-5", seed=state.seed)
    client = LLMClient(cfg)

    results: List[Dict] = []

    # -------------------------------------------------
    # 3) Run scene-by-scene fact checking
    # -------------------------------------------------
    for beat_id, scene in state.drafts.items():

        user = (
            user_tmpl
            .replace("{scene_id}", beat_id)
            .replace("{scene_text}", scene.text)
            .replace("{quotes}", str(quotes))
        )

        # LLM call
        data = client.complete_json(system, user, output_schema)

        # Coerce and patch missing fields
        obj = coerce_json(data) or {}
        obj.setdefault("scene_id", beat_id)
        obj.setdefault("claims", [])

        results.append(obj)

    # -------------------------------------------------
    # 4) Save to StoryState
    # -------------------------------------------------
    state.claim_graph = {
        "quotes": quotes,
        "claims_by_scene": results
    }

    return state
