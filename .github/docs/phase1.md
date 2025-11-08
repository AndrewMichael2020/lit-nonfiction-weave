# Phase 1 — Jupyter Prototype (Repo scaffold + minimal LangGraph path)

Scope: Implement minimal path **Planner → Draft → Fact → Revision**, add **Gemini‑backed ResearchAgent** for quotes/claims, enforce **3k–7.5k word band**, and **snapshot StoryState** with deterministic seeds. Target: Codespaces‑ready repo.

---

## 1) Repo layout (full listing)
```
lit-nf-stories/
  .devcontainer/
    devcontainer.json
    postCreate.sh
  .github/
    workflows/
      ci.yml
  notebooks/
    01_minimal_path.ipynb
    02_research_agent.ipynb
  src/
    __init__.py
    storygraph/
      __init__.py
      state.py
      router.py
      seeds.py
      schemas.py
      validators.py
      metrics.py
      persistence.py
      agents/
        __init__.py
        planner.py
        draft.py
        fact.py
        revision.py
        research.py
  prompts/
    planner.txt
    draft.txt
    fact.txt
    revision.txt
    research.txt
  templates/
    braided.json
    dual_timeline.json
    mosaic.json
    quest.json
  data/
    sources/  (user-provided pdfs/notes)
    runs/.gitkeep
  tests/
    test_metrics.py
    test_validators.py
  pyproject.toml
  requirements.txt
  README.md
  Makefile
  .gitignore
```

---

## 2) Devcontainer (Codespaces)
**.devcontainer/devcontainer.json**
```json
{
  "name": "lit-nf-stories",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "postCreateCommand": "bash .devcontainer/postCreate.sh",
  "features": {
    "ghcr.io/devcontainers/features/common-utils:2": {}
  }
}
```

**.devcontainer/postCreate.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade pip
pip install -r requirements.txt
python - <<'PY'
from pathlib import Path
Path('data/sources').mkdir(parents=True, exist_ok=True)
Path('data/runs').mkdir(parents=True, exist_ok=True)
print('Scaffold ready')
PY
```

---

## 3) Dependencies
**requirements.txt**
```
langgraph>=0.2.0
pydantic>=2.8
python-dotenv>=1.0
numpy>=1.26
pandas>=2.2
jupyterlab>=4.2
tiktoken>=0.7
rich>=13.7
sentencepiece>=0.2
```

(If using Google models later via third‑party SDKs, add those clients in Phase 1.5.)

**pyproject.toml** (minimal)
```toml
[project]
name = "lit-nf-stories"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []
```

---

## 4) Core data structures
**src/storygraph/state.py**
```python
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
```

**src/storygraph/seeds.py**
```python
PLANNER_SEED=137
RESEARCH_SEED=173
VOICE_SEED=191
DRAFT_SEED=223
FACT_SEED=251
RHYTHM_SEED=277
REVISION_SEED=311
```

**src/storygraph/schemas.py** (output schemas)
```python
PLANNER_SCHEMA = {
  "template": str,
  "beats": list,  # [{id, purpose, target_words}]
  "motifs": list
}
DRAFT_SCHEMA = {"scene_id": str, "text": str, "flags": list}
FACT_SCHEMA = {"links": list, "suggestions": list}
REVISION_SCHEMA = {"patches": list}
```

**src/storygraph/validators.py**
```python
import re

def total_words(text: str) -> int:
    return len(re.findall(r"\w+", text))

def within_band(n: int, lo: int, hi: int) -> bool:
    return lo <= n <= hi
```

**src/storygraph/metrics.py**
```python
from collections import Counter
import re

def sentence_lengths(text: str):
    sents = re.split(r"(?<=[.!?])\s+", text.strip()) if text.strip() else []
    return [len(s.split()) for s in sents if s]
```

**src/storygraph/persistence.py**
```python
import json, time
from pathlib import Path
from .state import StoryState

def save_state(state: StoryState, runs_dir: str = "data/runs") -> str:
    ts = int(time.time())
    path = Path(runs_dir) / f"state_{ts}.json"
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return str(path)
```

---

## 5) Minimal agents (stubs with deterministic behavior)
**src/storygraph/agents/planner.py**
```python
from ..state import StoryState, Outline, Beat
from ..seeds import PLANNER_SEED
import random

def run(state: StoryState) -> StoryState:
    random.seed(state.seed or PLANNER_SEED)
    # trivial braided outline with 4 beats
    beats = [
        Beat(id="s1", purpose="Introduce immediate tension", target_words=600),
        Beat(id="s2", purpose="Backstory complicates s1", target_words=500),
        Beat(id="s3", purpose="Context refracts s1", target_words=450),
        Beat(id="resolution", purpose="Earned reflection via scene", target_words=500),
    ]
    state.outline = Outline(template="braided", beats=beats, motifs=["{motif}"])
    return state
```

**src/storygraph/agents/draft.py**
```python
from ..state import StoryState, SceneDraft
from ..seeds import DRAFT_SEED
import random

def run(state: StoryState) -> StoryState:
    random.seed(state.seed or DRAFT_SEED)
    assert state.outline, "Planner must run first"
    drafts = {}
    for b in state.outline.beats:
        text = f"[SCENE {b.id}] Purpose: {b.purpose}. Lorem ipsum words " + "lorem " * (b.target_words//7)
        drafts[b.id] = SceneDraft(scene_id=b.id, text=text, flags=[])
    state.drafts = drafts
    state.draft_v1_concat = "\n\n".join(d.text for d in drafts.values())
    return state
```

**src/storygraph/agents/fact.py**
```python
from ..state import StoryState
from ..seeds import FACT_SEED

def run(state: StoryState) -> StoryState:
    # placeholder: mark no unsupported claims
    state.claim_graph = {"links": [], "suggestions": []}
    return state
```

**src/storygraph/agents/revision.py**
```python
from ..state import StoryState
from ..seeds import REVISION_SEED

def run(state: StoryState) -> StoryState:
    # placeholder: copy v1 to v2
    state.draft_v2_concat = state.draft_v1_concat
    return state
```

**src/storygraph/agents/research.py** (Gemini later; placeholder reads local notes)
```python
from ..state import StoryState
from pathlib import Path

def run(state: StoryState, sources_dir: str = "data/sources") -> StoryState:
    notes = []
    for p in Path(sources_dir).glob("*.txt"):
        notes.append({"file": p.name, "quote": p.read_text(encoding="utf-8")[:300]})
    state.claim_graph = {"quotes": notes, "claims": []}
    return state
```

---

## 6) LangGraph router (minimal path)
**src/storygraph/router.py**
```python
from .state import StoryState
from .agents import planner, draft, fact, revision, research
from .validators import total_words, within_band

class MinimalPipeline:
    def __init__(self, seed: int = 137):
        self.state = StoryState(seed=seed)

    def run(self, premise: str, venue: str):
        s = self.state
        s.premise, s.venue = premise, venue
        s = planner.run(s)
        s = draft.run(s)
        s = fact.run(s)
        s = revision.run(s)
        # simple word-band check
        n = total_words(s.draft_v2_concat)
        s.metrics["word_count_v2"] = n
        s.metrics["within_band"] = within_band(n, s.word_target_low, s.word_target_high)
        self.state = s
        return s
```

---

## 7) Notebook 01 — minimal path
**notebooks/01_minimal_path.ipynb** (outline)
```
1. Imports & display settings
2. Initialize pipeline with SEED=137
3. Provide premise + venue → run pipeline
4. Show outline beats
5. Preview draft_v1 and draft_v2 lengths
6. Word-band meter boolean
7. Save snapshot JSON under data/runs/
```

Sample cell (py):
```python
from storygraph.router import MinimalPipeline
from storygraph.persistence import save_state

pipe = MinimalPipeline(seed=137)
state = pipe.run(premise="{your premise}", venue="The New Yorker")
print(state.outline)
print(state.metrics)
print(save_state(state))
```

---

## 8) Notebook 02 — research agent (local placeholder → Gemini later)
```
1. Drop a few .txt files in data/sources
2. Run research.run(state) to attach quotes
3. Show claim_graph snippet
4. Export JSON story map (outline + claims)
```

---

## 9) Makefile
```make
setup:
	pip install -r requirements.txt

lab:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser

test:
	pytest -q
```

---

## 10) README (quick start)
- Open in Codespaces → container builds → Jupyter Lab.
- Run `notebooks/01_minimal_path.ipynb`.
- Add `.txt` notes to `data/sources` → run `02_research_agent.ipynb`.
- Snapshots saved to `data/runs/state_*.json`.

---

## 11) What’s next inside Phase 1
- Replace draft stub with real DraftAgent prompting (from Phase 0 prompts) and structured outputs.
- Implement word‑band enforcement per beat (±15%) and story total (3k–7.5k).
- Add deterministic seeding per agent from `seeds.py` to StoryState.
- Wire ResearchAgent to Gemini client when API ready; maintain same output schema.

Done. Spin up Codespaces, commit scaffold, and iterate inside notebooks.

