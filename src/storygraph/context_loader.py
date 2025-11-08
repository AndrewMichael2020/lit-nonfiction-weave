"""
Context loader: unified loader for codex, notes, and source materials.

This module consolidates all author-provided knowledge:
- docs/codex/*.md (people, places, claims, sources)
- docs/notes.md (fragments, hunches, voice reminders)
- data/sources/*.txt (full author intent documents)

Output is a structured context dict that agents can consume.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Tuple


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
CODEX_DIR = Path("docs/codex")
NOTES_PATH = Path("docs/notes.md")
SOURCES_DIR = Path("data/sources")


# -----------------------------------------------------------------------------
# Helper: parse markdown lists with [ID] prefix
# -----------------------------------------------------------------------------
_ID_PATTERN = re.compile(r"^\s*-\s*\[([A-Z]+\d+)\]\s*(.+)")  # Fixed: [A-Z]+ allows multi-letter IDs


def _parse_codex_md(md_path: Path) -> List[Tuple[str, str]]:
    """Parse markdown file with lines like: - [P1] Nikita Marwah — description"""
    items: List[Tuple[str, str]] = []
    if not md_path.exists():
        return items
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = _ID_PATTERN.match(line)
        if m:
            items.append((m.group(1).strip(), m.group(2).strip()))
    return items


# -----------------------------------------------------------------------------
# Load codex files
# -----------------------------------------------------------------------------
def load_codex() -> Dict[str, List[str]]:
    """
    Load docs/codex/*.md files and return structured lists.
    
    Returns:
        {
            "people": ["[P1] Nikita Marwah — ...", ...],
            "places": ["[PL1] Canadian Border Peak — ...", ...],
            "claims": ["[CL1] P1 climbed in BC 2020-2023", ...],
            "sources": ["[S1] GoFundMe announcement — ...", ...]
        }
    """
    def format_items(items: List[Tuple[str, str]]) -> List[str]:
        return [f"[{id_}] {text}" for id_, text in items]
    
    return {
        "people": format_items(_parse_codex_md(CODEX_DIR / "people.md")),
        "places": format_items(_parse_codex_md(CODEX_DIR / "places.md")),
        "claims": format_items(_parse_codex_md(CODEX_DIR / "claims.md")),
        "sources": format_items(_parse_codex_md(CODEX_DIR / "sources.md")),
    }


# -----------------------------------------------------------------------------
# Load notes.md
# -----------------------------------------------------------------------------
def load_notes() -> str:
    """
    Load docs/notes.md and return full text.
    
    Notes contain author fragments, hunches, voice reminders.
    Agents can use this for tone calibration and detail sourcing.
    """
    if not NOTES_PATH.exists():
        return ""
    return NOTES_PATH.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# Load source documents
# -----------------------------------------------------------------------------
def load_sources() -> Dict[str, str]:
    """
    Load all .txt files from data/sources/ directory.
    
    Returns:
        {
            "life_and_death_of_a_climber": "AUTHOR INTENT...(full text)...",
            "kyiv_water_outages": "...",
        }
    """
    sources = {}
    if not SOURCES_DIR.exists():
        return sources
    
    for fpath in SOURCES_DIR.glob("*.txt"):
        sources[fpath.stem] = fpath.read_text(encoding="utf-8")
    
    return sources


# -----------------------------------------------------------------------------
# Unified context builder
# -----------------------------------------------------------------------------
def load_all_context() -> Dict:
    """
    Load all available context: codex + notes + sources.
    
    Returns:
        {
            "codex": {
                "people": [...],
                "places": [...],
                "claims": [...],
                "sources": [...]
            },
            "notes": "full notes.md text",
            "sources": {
                "life_and_death_of_a_climber": "...",
                ...
            }
        }
    """
    return {
        "codex": load_codex(),
        "notes": load_notes(),
        "sources": load_sources(),
    }


# -----------------------------------------------------------------------------
# Formatting helpers for prompt injection
# -----------------------------------------------------------------------------
def format_codex_for_prompt(codex: Dict[str, List[str]], max_items_per_category: int = 20) -> str:
    """
    Format codex into a compact text block suitable for LLM prompts.
    
    Example output:
        PEOPLE:
        [P1] Nikita Marwah — petite climber, active 2020-2023
        [P2] Chris — climbing partner, died on Atwell Peak
        
        PLACES:
        [PL1] Canadian Border Peak — site of Nikita's final climb
        ...
    """
    lines = []
    
    if codex.get("people"):
        lines.append("PEOPLE:")
        for item in codex["people"][:max_items_per_category]:
            lines.append(item)
        lines.append("")
    
    if codex.get("places"):
        lines.append("PLACES:")
        for item in codex["places"][:max_items_per_category]:
            lines.append(item)
        lines.append("")
    
    if codex.get("claims"):
        lines.append("VERIFIED CLAIMS:")
        for item in codex["claims"][:max_items_per_category]:
            lines.append(item)
        lines.append("")
    
    if codex.get("sources"):
        lines.append("SOURCES:")
        for item in codex["sources"][:max_items_per_category]:
            lines.append(item)
        lines.append("")
    
    return "\n".join(lines).strip()


def extract_notes_fragments(notes: str, max_chars: int = 800) -> str:
    """
    Extract key fragments from notes.md for prompt conditioning.
    
    Prioritizes:
    - Fragments section (concrete sensory details)
    - Voice reminders (tone/style guidance)
    
    Returns compact string suitable for prompt injection.
    """
    if not notes:
        return ""
    
    # Look for ## Fragments section
    fragments = []
    voice_reminders = []
    
    lines = notes.splitlines()
    current_section = None
    
    for line in lines:
        if line.startswith("## Fragments"):
            current_section = "fragments"
            continue
        elif line.startswith("## Voice Reminders"):
            current_section = "voice"
            continue
        elif line.startswith("##"):
            current_section = None
            continue
        
        if current_section == "fragments" and line.strip().startswith("-"):
            fragments.append(line.strip())
        elif current_section == "voice" and line.strip().startswith("-"):
            voice_reminders.append(line.strip())
    
    result = []
    if fragments:
        result.append("AUTHOR FRAGMENTS:")
        result.extend(fragments[:10])  # Limit to 10 fragments
    if voice_reminders:
        result.append("\nVOICE GUIDANCE:")
        result.extend(voice_reminders[:5])  # Limit to 5 reminders
    
    output = "\n".join(result)
    if len(output) > max_chars:
        output = output[:max_chars] + "..."
    
    return output
