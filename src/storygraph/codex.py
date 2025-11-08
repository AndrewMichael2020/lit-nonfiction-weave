from __future__ import annotations
import json, re
from pathlib import Path
from typing import Dict, List, Tuple

CODex_DIR = Path("docs/codex")
CODex_JSON = Path("data/codex.json")

_ID = re.compile(r"^\s*-\s*\[([A-Za-z]\d+)\]\s*(.+?)\s*$")

def _parse_list(md_path: Path) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    if not md_path.exists():
        return items
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = _ID.match(line)
        if m:
            items.append((m.group(1).strip(), m.group(2).strip()))
    return items

def load_codex() -> Dict:
    claims = _parse_list(CODex_DIR / "claims.md")
    sources = _parse_list(CODex_DIR / "sources.md")
    people = _parse_list(CODex_DIR / "people.md")
    places = _parse_list(CODex_DIR / "places.md")
    data = {
        "claims": [{"id": i, "text": t, "status": "asserted"} for i, t in claims],
        "sources": [{"id": i, "label": t} for i, t in sources],
        "people": [{"id": i, "label": t} for i, t in people],
        "places": [{"id": i, "label": t} for i, t in places],
    }
    CODex_JSON.parent.mkdir(parents=True, exist_ok=True)
    CODex_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data

def get_codex_json() -> Dict:
    if CODex_JSON.exists():
        return json.loads(CODex_JSON.read_text(encoding="utf-8"))
    return load_codex()

