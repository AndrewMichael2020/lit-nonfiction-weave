from __future__ import annotations
from pathlib import Path

NOTES = Path("docs/notes.md")
SEED_TAG = "<!-- AGENT-SEED-LOCK -->"

SEED_BLOCK = f"""\
{SEED_TAG}
[seed] Imported by pipeline: notes indexed for Planner/Draft/Fact.
After this line, agents treat docs/notes.md as read-only. Authors may edit freely.
{SEED_TAG}
"""

def ensure_seed_block() -> None:
    text = NOTES.read_text(encoding="utf-8") if NOTES.exists() else ""
    if SEED_TAG not in text:
        NOTES.write_text(SEED_BLOCK + "\n" + text, encoding="utf-8")
