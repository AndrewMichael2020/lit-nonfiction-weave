from __future__ import annotations
import json, re, pathlib
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

def _strip_fences(txt: str) -> str:
    t = txt.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t

def _promote_flags_to_claims(obj: Dict) -> Dict:
    """If no 'claims' but there is 'flags': [{'span':..., 'type':'fact'}...], promote to claims"""
    if obj.get("claims"):
        return obj
    flags = obj.get("flags") or []
    claims = []
    for f in flags:
        if isinstance(f, dict) and f.get("type") == "fact":
            txt = f.get("span") or f.get("text") or ""
            if txt:
                claims.append({"claim": txt, "substantiated": False, "evidence_ids": []})
    if claims:
        obj["claims"] = claims
    return obj


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
    assert model, "Fact agent requires model parameter from centralized config"
    system, output_schema, user_tmpl = _split(PROMPT)

    cfg = LLMConfig(model=model, seed=state.seed)
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
            .replace("{quotes}", json.dumps(quotes, ensure_ascii=False))
        )

        # LLM call
        data = client.complete_json(system, user, output_schema)

        # Coerce and sanitize
        if isinstance(data, str):
            data = _strip_fences(data)
            try:
                data = json.loads(data)
            except Exception:
                data = {}
        
        obj = coerce_json(data) or {}
        obj = _promote_flags_to_claims(obj)

        # Minimal guard: ensure keys
        obj.setdefault("scene_id", beat_id)
        obj.setdefault("claims", [])

        # Debug count
        print(f"[FACT DEBUG] Scene {beat_id}: claims={len(obj['claims'])}")
        if obj.get('claims'):
            print(f"[FACT DEBUG] First claim: {obj['claims'][0]}")

        results.append(obj)

    # -------------------------------------------------
    # 4) Save to StoryState
    # -------------------------------------------------
    print(f"[FACT DEBUG] Saving claim_graph with {len(results)} scenes")
    total_claims = sum(len(r.get('claims', [])) for r in results)
    print(f"[FACT DEBUG] Total claims across all scenes: {total_claims}")
    
    state.claim_graph = {
        "quotes": quotes,
        "claims_by_scene": results
    }

    return state
