# src/storygraph/validators.py
import re
from typing import Dict

WORD = re.compile(r"\w+")

def total_words(text: str) -> int:
    return len(WORD.findall(text or ""))

def within_band(n: int, lo: int, hi: int) -> bool:
    return lo <= n <= hi

def beat_within_tolerance(actual: int, target: int, tol: float = 0.15) -> bool:
    # Use target-based tolerance to keep quotas meaningful
    return abs(actual - target) <= target * tol

def audit_beats(drafts: Dict[str, str], targets: Dict[str, int], tol: float = 0.15) -> Dict[str, bool]:
    return {sid: beat_within_tolerance(total_words(txt), targets.get(sid, 0), tol)
            for sid, txt in drafts.items()}
