# src/storygraph/agents/draft.py
from __future__ import annotations
from pathlib import Path
from typing import Dict
from ..state import StoryState, SceneDraft
from ..llm import LLMClient, LLMConfig
import json

# prompts live at src/prompts/draft.txt (go up to repo root then into src/prompts)
PROMPT_PATH = Path(__file__).resolve().parents[3] / "src" / "prompts" / "draft.txt"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

def _split(prompt: str):
    sys = prompt.split("[system]\n", 1)[1].split("[output_schema]", 1)[0].strip()
    schema = prompt.split("[output_schema]\n", 1)[1].split("[user]", 1)[0].strip()
    user = prompt.split("[user]\n", 1)[1].strip()
    return sys, schema, user

def run(
    state: StoryState,
    model: str = "anthropic/claude-opus-4-1-20250805",
    voice_matrix: Dict | None = None,
    vernacular_inline: str = "",
) -> StoryState:
    assert state.outline, "Planner must run first"
    system, output_schema, user_tmpl = _split(PROMPT)

    client = LLMClient(LLMConfig(model=model, seed=state.seed))
    drafts: Dict[str, SceneDraft] = {}

    for b in state.outline.beats:
        user = (
            user_tmpl.replace("{beat_id}", b.id)
            .replace("{purpose}", b.purpose)
            .replace("{n}", str(b.target_words))
            .replace("{motifs}", ",".join(state.outline.motifs or []))
            .replace("{voice}", json.dumps(voice_matrix or {}))
            .replace("{vernacular_inline}", vernacular_inline)
        )
        obj = client.complete_json(system, user, output_schema)

        # hard guard: require 'text'
        if "text" not in obj:
            raise RuntimeError(
                f"DraftAgent: model did not return 'text'. Got keys: {list(obj.keys())}. Raw: {str(obj)[:400]}"
            )

        drafts[b.id] = SceneDraft(
            scene_id=obj.get("scene_id", b.id),
            text=obj["text"],
            flags=obj.get("flags", []),
        )

    state.drafts = drafts
    state.draft_v1_concat = "\n\n".join(d.text for d in drafts.values())
    return state
