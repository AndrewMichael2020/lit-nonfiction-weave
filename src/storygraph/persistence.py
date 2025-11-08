import json, time
from pathlib import Path
from .state import StoryState


def save_state(state: StoryState, runs_dir: str = "data/runs") -> str:
    ts = int(time.time())
    path = Path(runs_dir) / f"state_{ts}.json"
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return str(path)
