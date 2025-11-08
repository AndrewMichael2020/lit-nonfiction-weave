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
           codex: str = "", notes_fragments: str = "") -> str:
    return (user_tmpl
            .replace("{premise}", premise)
            .replace("{venue}", venue)
            .replace("{preferred}", preferred)
            .replace("{codex}", codex)
            .replace("{notes_fragments}", notes_fragments))

def run(state: StoryState, model: str = None, context: dict = None) -> StoryState:
    assert model, "Planner agent requires model parameter from centralized config"
    
    print("\n[PLANNER] Starting planner agent...")
    print(f"[PLANNER] Model: {model}")
    
    system, output_schema, user_tmpl = _split(PROMPT)
    
    # Extract context for prompt
    codex_text = ""
    notes_fragments = ""
    if context:
        from ..context_loader import format_codex_for_prompt, extract_notes_fragments
        if "codex" in context:
            codex_text = format_codex_for_prompt(context["codex"])
            print(f"[PLANNER] Codex context: {len(codex_text)} chars")
        if "notes" in context:
            notes_fragments = extract_notes_fragments(context["notes"])
            print(f"[PLANNER] Notes fragments: {len(notes_fragments)} chars")
    
    user = render(user_tmpl, state.premise, state.venue, 
                  codex=codex_text, notes_fragments=notes_fragments)
    
    print(f"[PLANNER] System prompt: {len(system)} chars")
    print(f"[PLANNER] User prompt: {len(user)} chars")
    print(f"[PLANNER] Calling LLM...")
    obj = LLMClient(LLMConfig(model=model, seed=state.seed)).complete_json(system, user, output_schema)

    if "beats" not in obj or "template" not in obj:
        raise RuntimeError(f"Planner: missing required keys. Got: {list(obj.keys())}")

    print(f"[PLANNER] ✓ Generated {len(obj['beats'])} beats using template: {obj.get('template')}")
    
    beats = [Beat(id=str(b["id"]), purpose=b["purpose"], target_words=int(b["target_words"]))
             for b in obj["beats"]]
    state.outline = Outline(template=obj["template"], beats=beats, motifs=obj.get("motifs", []))
    return state
