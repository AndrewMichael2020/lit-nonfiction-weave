from __future__ import annotations
import pathlib
from ..state import StoryState
from ..llm import LLMClient, LLMConfig
from ..json_utils import coerce_json


import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
PROMPT = (ROOT / "src" / "prompts" / "revision.txt").read_text(encoding="utf-8")

def run(
    state: StoryState, model: str = None, targets=None, scope: str = "story"
) -> StoryState:
    system, output_schema, user_tmpl = _split(PROMPT)
    cfg = LLMConfig(model=model or "anthropic/claude-sonnet-4-5-20250929", seed=state.seed)
    client = LLMClient(cfg)
    user = (
        user_tmpl.replace("{g}", "0.6")
        .replace("{c}", "0.2")
        .replace("{w}", "0.4")
        .replace("{i}", "0.2")
        .replace("{r}", "0.5")
        .replace("{scope}", scope)
        .replace("{text}", state.draft_v1_concat)
    )
    data = client.complete_json(system, user, output_schema)
    obj = coerce_json(data)
    # naive: apply patches if any, else copy v1
    if obj.get("patches"):
        state.draft_v2_concat = state.draft_v1_concat  # patch application TBD
    else:
        state.draft_v2_concat = state.draft_v1_concat
    return state


def _split(prompt: str):
    sys = prompt.split("[system]\n", 1)[1].split("[output_schema]", 1)[0].strip()
    schema = prompt.split("[output_schema]\n", 1)[1].split("[user]", 1)[0].strip()
    user = prompt.split("[user]\n", 1)[1].strip()
    return sys, schema, user
