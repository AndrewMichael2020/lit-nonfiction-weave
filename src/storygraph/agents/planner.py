# src/storygraph/agents/planner.py
from __future__ import annotations
from pathlib import Path
from ..state import StoryState, Outline, Beat
from ..llm import LLMClient, LLMConfig

PROMPT_PATH = Path(__file__).resolve().parents[3] / "src" / "prompts" / "planner.txt"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

def _split(prompt: str):
    sys = prompt.split("[system]\n", 1)[1].split("[output_schema]", 1)[0].strip()
    schema = prompt.split("[output_schema]\n", 1)[1].split("[user]", 1)[0].strip()
    user = prompt.split("[user]\n", 1)[1].strip()
    return sys, schema, user

def render(user_tmpl: str, premise: str, venue: str,
           preferred: str = "braided|dual_timeline",
           source_tags: str = "", voice_tags: str = "", constraints: str = "") -> str:
    return (user_tmpl
            .replace("{premise}", premise)
            .replace("{venue}", venue)
            .replace("{preferred}", preferred)
            .replace("{source_tags}", source_tags)
            .replace("{voice_tags}", voice_tags)
            .replace("{constraints}", constraints))

def run(state: StoryState, model: str = None) -> StoryState:
    assert model, "Planner agent requires model parameter from centralized config"
    system, output_schema, user_tmpl = _split(PROMPT)
    user = render(user_tmpl, state.premise, state.venue)
    obj = LLMClient(LLMConfig(model=model, seed=state.seed)).complete_json(system, user, output_schema)

    if "beats" not in obj or "template" not in obj:
        raise RuntimeError(f"Planner: missing required keys. Got: {list(obj.keys())}")

    beats = [Beat(id=str(b["id"]), purpose=b["purpose"], target_words=int(b["target_words"]))
             for b in obj["beats"]]
    state.outline = Outline(template=obj["template"], beats=beats, motifs=obj.get("motifs", []))
    return state
