from __future__ import annotations
from ..state import StoryState
from pathlib import Path


def run(state: StoryState, sources_dir: str = "data/sources") -> StoryState:
    notes = []
    for p in Path(sources_dir).glob("*.txt"):
        notes.append(
            {"id": p.stem, "file": p.name, "quote": p.read_text(encoding="utf-8")[:300]}
        )
    state.claim_graph = {"quotes": notes, "claims": []}
    return state
