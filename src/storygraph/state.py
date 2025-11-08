from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Beat(BaseModel):
    id: str
    purpose: str
    target_words: int


class Outline(BaseModel):
    template: str
    beats: List[Beat]
    motifs: List[str] = []


class SceneDraft(BaseModel):
    scene_id: str
    text: str
    flags: List[Dict[str, Any]] = []


class StoryState(BaseModel):
    seed: int = Field(default=137)
    premise: str = ""
    venue: str = ""
    outline: Optional[Outline] = None
    drafts: Dict[str, SceneDraft] = {}
    draft_v1_concat: str = ""
    draft_v2_concat: str = ""
    claim_graph: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    word_target_low: int = 3000
    word_target_high: int = 7500
