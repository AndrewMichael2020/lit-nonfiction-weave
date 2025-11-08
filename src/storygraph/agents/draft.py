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
    model: str = None,
    context: dict = None,
) -> StoryState:
    assert state.outline, "Planner must run first"
    assert model, "Draft agent requires model parameter from centralized config"
    
    print("\n[DRAFT] Starting draft agent...")
    print(f"[DRAFT] Model: {model}")
    print(f"[DRAFT] Beats to draft: {len(state.outline.beats)}")
    
    system, output_schema, user_tmpl = _split(PROMPT)

    # Extract context for prompt
    codex_text = ""
    notes_fragments = ""
    if context:
        from ..context_loader import format_codex_for_prompt, extract_notes_fragments
        if "codex" in context:
            codex_text = format_codex_for_prompt(context["codex"])
            print(f"[DRAFT] Codex context: {len(codex_text)} chars")
        if "notes" in context:
            notes_fragments = extract_notes_fragments(context["notes"])
            print(f"[DRAFT] Notes fragments: {len(notes_fragments)} chars")

    client = LLMClient(LLMConfig(model=model, seed=state.seed))
    drafts: Dict[str, SceneDraft] = {}

    for i, b in enumerate(state.outline.beats, 1):
        print(f"[DRAFT] Beat {i}/{len(state.outline.beats)}: {b.id} ({b.target_words} words)")
        
        user = (
            user_tmpl.replace("{beat_id}", b.id)
            .replace("{purpose}", b.purpose)
            .replace("{n}", str(b.target_words))
            .replace("{motifs}", ",".join(state.outline.motifs or []))
            .replace("{codex}", codex_text)
            .replace("{notes_fragments}", notes_fragments)
        )
        
        print(f"[DRAFT]   Prompt: {len(user)} chars, calling LLM...")
        obj = client.complete_json(system, user, output_schema)

        # hard guard: require 'text'
        if "text" not in obj:
            raise RuntimeError(
                f"DraftAgent: model did not return 'text'. Got keys: {list(obj.keys())}. Raw: {str(obj)[:400]}"
            )

        word_count = len(obj["text"].split())
        print(f"[DRAFT]   ✓ Generated {word_count} words")
        
        drafts[b.id] = SceneDraft(
            scene_id=obj.get("scene_id", b.id),
            text=obj["text"],
            flags=obj.get("flags", []),
        )

    state.drafts = drafts
    state.draft_v1_concat = "\n\n".join(d.text for d in drafts.values())
    
    total_words = len(state.draft_v1_concat.split())
    print(f"[DRAFT] ✓ Complete: {len(drafts)} scenes, {total_words} total words")
    
    return state
