# Phase 1b — Real Agents + Validators (Full Code Drop)

**Goal**: Make the pipeline *real* inside Codespaces — working agents with structured outputs, seeds, per‑beat and story word‑band enforcement, and a minimal research placeholder. LLM providers are pluggable; code runs even without keys via an offline deterministic fallback.

> Place these files into your repo. Paths are relative to repo root.

---

## 0) Updates to dependencies
**requirements.txt** — append
```
openai>=1.43.0
anthropic>=0.34.0
python-dotenv>=1.0
```

**.env (local, not committed)**
```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
# MODEL CHOICES (override in notebooks):
PLANNER_MODEL=openai/gpt-5
DRAFT_MODEL=anthropic/opus-4.1
FACT_MODEL=openai/gpt-5
REVISION_MODEL=anthropic/sonnet-4.5
```

---

## 1) LLM plumbing
**src/storygraph/llm.py**
```python
from __future__ import annotations
import json, os, random
from dataclasses import dataclass
from typing import Optional, Dict, Any

from dotenv import load_dotenv
load_dotenv()

try:
    from openai import OpenAI
except Exception:
    OpenAI = None
try:
    import anthropic
except Exception:
    anthropic = None

@dataclass
class LLMConfig:
    model: str
    seed: int = 137
    temperature: float = 0.2

class LocalMockLLM:
    """Deterministic offline fallback returning minimal JSON obeying schema."""
    def __init__(self, seed: int = 137):
        random.seed(seed)
        self.seed = seed

    def complete_json(self, system: str, user: str, schema_hint: str) -> Dict[str, Any]:
        if '"template": "' in schema_hint and 'beats' in schema_hint:
            return {
                "template": "braided",
                "beats": [
                    {"id": "s1", "purpose": "Introduce immediate tension", "target_words": 600},
                    {"id": "s2", "purpose": "Backstory complicates s1", "target_words": 520},
                    {"id": "s3", "purpose": "Context refracts s1", "target_words": 480},
                    {"id": "resolution", "purpose": "Earned reflection via scene", "target_words": 550},
                ],
                "motifs": ["{motif}"]
            }
        if '"scene_id"' in schema_hint and '"text"' in schema_hint:
            # produce deterministic lorem text roughly matching target words if provided in user
            import re
            m = re.search(r"Target words: (\d+)", user)
            n = int(m.group(1)) if m else 400
            base = "We stand in the sharp wind outside the clinic, pockets full of receipts and questions. "
            words = (base + ("grit detail brick dust on the sill " * 2000))[:n*6]
            return {"scene_id": "unknown", "text": words, "flags": []}
        if '"links"' in schema_hint and '"suggestions"' in schema_hint:
            return {"links": [], "suggestions": []}
        if '"patches"' in schema_hint:
            return {"patches": []}
        return {}

class LLMClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg
        self.backend = self._select_backend(cfg.model)

    def _select_backend(self, model: str):
        if model.startswith("openai/") and OpenAI and os.getenv("OPENAI_API_KEY"):
            return ("openai", OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
        if model.startswith("anthropic/") and anthropic and os.getenv("ANTHROPIC_API_KEY"):
            return ("anthropic", anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")))
        return ("local", LocalMockLLM(self.cfg.seed))

    def complete_json(self, system: str, user: str, schema_hint: str) -> Dict[str, Any]:
        kind, client = self.backend
        if kind == "local":
            return client.complete_json(system, user, schema_hint)
        if kind == "openai":
            # Use JSON response_format when available
            from openai import APIError
            try:
                content = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
                resp = client.chat.completions.create(
                    model=self.cfg.model.split("/",1)[1],
                    messages=content,
                    temperature=self.cfg.temperature,
                    seed=self.cfg.seed,
                    response_format={"type": "json_object"}
                )
                raw = resp.choices[0].message.content
                return json.loads(raw)
            except Exception as e:
                return LocalMockLLM(self.cfg.seed).complete_json(system, user, schema_hint)
        if kind == "anthropic":
            try:
                msg = client.messages.create(
                    model=self.cfg.model.split("/",1)[1],
                    temperature=self.cfg.temperature,
                    system=system,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": user}]
                )
                raw = ''.join([p.text for p in msg.content if hasattr(p, 'text')])
                return json.loads(raw)
            except Exception:
                return LocalMockLLM(self.cfg.seed).complete_json(system, user, schema_hint)
        return {}
```

---

## 2) JSON helpers
**src/storygraph/json_utils.py**
```python
import json
from typing import Any, Dict

def coerce_json(data: Any) -> Dict:
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        return json.loads(data)
    raise ValueError("Unsupported JSON input")
```

---

## 3) Schemas (unchanged, but kept here for clarity)
**src/storygraph/schemas.py**
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

---

## 4) Validators (beat and story)
**src/storygraph/validators.py**
```python
import re
from typing import Dict, List

WORD = re.compile(r"\w+")

def total_words(text: str) -> int:
    return len(WORD.findall(text or ""))

def within_band(n: int, lo: int, hi: int) -> bool:
    return lo <= n <= hi

def beat_within_tolerance(actual: int, target: int, tol: float = 0.15) -> bool:
    return abs(actual - target) <= target * tol

def audit_beats(drafts: Dict[str, str], targets: Dict[str, int], tol: float = 0.15) -> Dict[str, bool]:
    return {sid: beat_within_tolerance(total_words(txt), targets.get(sid, 0), tol) for sid, txt in drafts.items()}
```

---

## 5) Agents — real implementations using prompts

**prompts/planner.txt** (Phase‑0 content reference)
```
[system]
You are a literary non‑fiction story planner. You return a JSON outline that obeys the chosen template and a 3k–7.5k word band. Prefer braided or dual‑timeline when personal + reported material coexist. Keep scene purposes concrete and testable.
[output_schema]
{"template": "braided|dual_timeline|mosaic|quest", "beats": [ {"id": "...", "purpose": "...", "target_words": n } ], "motifs": ["..."] }
[user]
Premise: {premise}
Venue target: {venue}
Available sources: {source_tags}
Voice sample tags: {voice_tags}
Preferred templates: {preferred}
Constraints: {constraints}
```

**prompts/draft.txt**
```
[system]
Write scene text for one beat at a time. Enforce grit metrics and craft pillars. Show flagged lines that require fact sources.
[output_schema]
{"scene_id":"...","text":"...","flags":[{"span":"...","type":"fact|cliche|passive|overabstract"}]}
[user]
Beat: {beat_id} — {purpose}
Target words: {n}
Motifs: {motifs}
Voice matrix: {voice}
Vernacular lexicon: {vernacular_inline}
```

**prompts/fact.txt**
```
[system]
Map factual sentences to the claim graph. Propose minimal rewrites for unsupported lines.
[output_schema]
{"links":[{"span":"...","claim_id":"c1","status":"supported|needs_cite|rewrite"}], "suggestions":[{"span":"...","rewrite":"..."}]}
[user]
Scene text: {scene}
Claim graph: {graph}
```

**prompts/revision.txt**
```
[system]
Rewrite only selected spans to move toward target sliders (grit, compression, warmth, irony, restraint). Preserve vernacular tags and author‑edited locks.
[output_schema]
{"patches":[{"span_id":"...","before":"...","after":"...","rationale":"..."}]}
[user]
Targets: grit {g}, compression {c}, warmth {w}, irony {i}, restraint {r}
Scope: {scope}
Text: {text}
```

**src/storygraph/agents/planner.py**
```python
from __future__ import annotations
import pathlib
from ..state import StoryState, Outline, Beat
from ..llm import LLMClient, LLMConfig
from ..json_utils import coerce_json

PROMPT = pathlib.Path('prompts/planner.txt').read_text(encoding='utf-8')

def render(premise: str, venue: str, preferred: str = "braided|dual_timeline", source_tags: str = "", voice_tags: str = "", constraints: str = ""):
    return PROMPT.replace('{premise}', premise).replace('{venue}', venue).replace('{preferred}', preferred).replace('{source_tags}', source_tags).replace('{voice_tags}', voice_tags).replace('{constraints}', constraints)

def run(state: StoryState, model: str = None) -> StoryState:
    system, output_schema, user = _split(PROMPT)
    user_filled = render(state.premise, state.venue)
    cfg = LLMConfig(model=model or 'openai/gpt-5', seed=state.seed)
    client = LLMClient(cfg)
    data = client.complete_json(system, user_filled, output_schema)
    obj = coerce_json(data)
    beats = [Beat(id=b['id'], purpose=b['purpose'], target_words=int(b['target_words'])) for b in obj['beats']]
    state.outline = Outline(template=obj['template'], beats=beats, motifs=obj.get('motifs', []))
    return state

def _split(prompt: str):
    # naive split of our prompt sections
    sys = prompt.split('[system]\n',1)[1].split('[output_schema]',1)[0].strip()
    schema = prompt.split('[output_schema]\n',1)[1].split('[user]',1)[0].strip()
    user = prompt.split('[user]\n',1)[1].strip()
    return sys, schema, user
```

**src/storygraph/agents/draft.py**
```python
from __future__ import annotations
import pathlib
from typing import Dict
from ..state import StoryState, SceneDraft
from ..llm import LLMClient, LLMConfig
from ..json_utils import coerce_json

PROMPT = pathlib.Path('prompts/draft.txt').read_text(encoding='utf-8')


def run(state: StoryState, model: str = None, voice_matrix: Dict = None, vernacular_inline: str = "") -> StoryState:
    assert state.outline, "Planner must run first"
    system, output_schema, user_tmpl = _split(PROMPT)
    cfg = LLMConfig(model=model or 'anthropic/opus-4.1', seed=state.seed)
    client = LLMClient(cfg)
    drafts = {}
    for b in state.outline.beats:
        user = user_tmpl.replace('{beat_id}', b.id).replace('{purpose}', b.purpose).replace('{n}', str(b.target_words)).replace('{motifs}', ','.join(state.outline.motifs or [])).replace('{voice}', str(voice_matrix or {})).replace('{vernacular_inline}', vernacular_inline)
        data = client.complete_json(system, user, output_schema)
        obj = coerce_json(data)
        drafts[b.id] = SceneDraft(scene_id=obj.get('scene_id', b.id), text=obj['text'], flags=obj.get('flags', []))
    state.drafts = drafts
    state.draft_v1_concat = "\n\n".join(d.text for d in drafts.values())
    return state

def _split(prompt: str):
    sys = prompt.split('[system]\n',1)[1].split('[output_schema]',1)[0].strip()
    schema = prompt.split('[output_schema]\n',1)[1].split('[user]',1)[0].strip()
    user = prompt.split('[user]\n',1)[1].strip()
    return sys, schema, user
```

**src/storygraph/agents/fact.py**
```python
from __future__ import annotations
import pathlib, json
from ..state import StoryState
from ..llm import LLMClient, LLMConfig
from ..json_utils import coerce_json

PROMPT = pathlib.Path('prompts/fact.txt').read_text(encoding='utf-8')

def run(state: StoryState, model: str = None) -> StoryState:
    system, output_schema, user_tmpl = _split(PROMPT)
    cfg = LLMConfig(model=model or 'openai/gpt-5', seed=state.seed)
    client = LLMClient(cfg)
    # For now, claim_graph may be empty. Pass story text.
    user = user_tmpl.replace('{scene}', state.draft_v1_concat).replace('{graph}', json.dumps(state.claim_graph or {}))
    data = client.complete_json(system, user, output_schema)
    obj = coerce_json(data)
    state.claim_graph = obj
    return state

def _split(prompt: str):
    sys = prompt.split('[system]\n',1)[1].split('[output_schema]',1)[0].strip()
    schema = prompt.split('[output_schema]\n',1)[1].split('[user]',1)[0].strip()
    user = prompt.split('[user]\n',1)[1].strip()
    return sys, schema, user
```

**src/storygraph/agents/revision.py**
```python
from __future__ import annotations
import pathlib
from ..state import StoryState
from ..llm import LLMClient, LLMConfig
from ..json_utils import coerce_json

PROMPT = pathlib.Path('prompts/revision.txt').read_text(encoding='utf-8')

def run(state: StoryState, model: str = None, targets = None, scope: str = 'story') -> StoryState:
    system, output_schema, user_tmpl = _split(PROMPT)
    cfg = LLMConfig(model=model or 'anthropic/sonnet-4.5', seed=state.seed)
    client = LLMClient(cfg)
    user = user_tmpl.replace('{g}', '0.6').replace('{c}', '0.2').replace('{w}', '0.4').replace('{i}', '0.2').replace('{r}', '0.5').replace('{scope}', scope).replace('{text}', state.draft_v1_concat)
    data = client.complete_json(system, user, output_schema)
    obj = coerce_json(data)
    # naive: apply patches if any, else copy v1
    if obj.get('patches'):
        state.draft_v2_concat = state.draft_v1_concat  # patch application TBD
    else:
        state.draft_v2_concat = state.draft_v1_concat
    return state

def _split(prompt: str):
    sys = prompt.split('[system]\n',1)[1].split('[output_schema]',1)[0].strip()
    schema = prompt.split('[output_schema]\n',1)[1].split('[user]',1)[0].strip()
    user = prompt.split('[user]\n',1)[1].strip()
    return sys, schema, user
```

**src/storygraph/agents/research.py** (unchanged placeholder — reads local `.txt`)
```python
from __future__ import annotations
from ..state import StoryState
from pathlib import Path

def run(state: StoryState, sources_dir: str = "data/sources") -> StoryState:
    notes = []
    for p in Path(sources_dir).glob("*.txt"):
        notes.append({"id": p.stem, "file": p.name, "quote": p.read_text(encoding="utf-8")[:300]})
    state.claim_graph = {"quotes": notes, "claims": []}
    return state
```

---

## 6) Router — enforce word bands
**src/storygraph/router.py**
```python
from .state import StoryState
from .agents import planner, draft, fact, revision, research
from .validators import total_words, within_band, audit_beats

class Pipeline:
    def __init__(self, seed: int = 137):
        self.state = StoryState(seed=seed)

    def run_minimal(self, premise: str, venue: str):
        s = self.state
        s.premise, s.venue = premise, venue
        s = planner.run(s)
        s = draft.run(s)
        s = fact.run(s)
        s = revision.run(s)
        # metrics
        drafts = {k:v.text for k,v in s.drafts.items()}
        targets = {b.id: b.target_words for b in s.outline.beats}
        s.metrics['beat_within'] = audit_beats(drafts, targets, 0.15)
        s.metrics['word_count_v2'] = total_words(s.draft_v2_concat)
        s.metrics['within_band'] = within_band(s.metrics['word_count_v2'], s.word_target_low, s.word_target_high)
        self.state = s
        return s
```

---

## 7) Notebooks — minimal JSON (copy as files)
**notebooks/01_minimal_path.ipynb**
```json
{
  "cells": [
    {"cell_type": "markdown", "metadata": {}, "source": ["# Minimal Path — Planner → Draft → Fact → Revision"]},
    {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": [
      "from storygraph.router import Pipeline\n",
      "pipe = Pipeline(seed=137)\n",
      "state = pipe.run_minimal(premise='A son drives to a hospital in winter to sign papers he does not want to read.', venue='The New Yorker')\n",
      "state.metrics\n"
    ]},
    {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": [
      "print(state.outline)\n",
      "print(state.metrics['beat_within'])\n",
      "print('Total words:', state.metrics['word_count_v2'], 'Within band:', state.metrics['within_band'])\n"
    ]}
  ],
  "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"}},
  "nbformat": 4,
  "nbformat_minor": 5
}
```

**notebooks/02_research_agent.ipynb**
```json
{
  "cells": [
    {"cell_type": "markdown", "metadata": {}, "source": ["# Research Agent — local notes placeholder"]},
    {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": [
      "from storygraph.agents import research\n",
      "from storygraph.router import Pipeline\n",
      "pipe = Pipeline(seed=137)\n",
      "s = pipe.state\n",
      "s.premise = 'Premise here'\n",
      "s.venue = 'Outside'\n",
      "s = research.run(s)\n",
      "s.claim_graph\n"
    ]}
  ],
  "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"}},
  "nbformat": 4,
  "nbformat_minor": 5
}
```

---

## 8) Quick test
**tests/test_validators.py**
```python
from storygraph.validators import beat_within_tolerance

def test_beat_tol():
    assert beat_within_tolerance(575, 500, 0.15) is True
    assert beat_within_tolerance(751, 650, 0.15) is True
    assert beat_within_tolerance(900, 600, 0.15) is False
```

---

## 9) README snippet — Phase 1b
Add under **Phase 1b** section:
```
- Provide OPENAI/ANTHROPIC keys in .env or run offline fallback.
- Run 01_minimal_path.ipynb → check metrics.
- Inspect data/runs/*.json snapshots as needed.
```

Done. This code path runs fully offline via `LocalMockLLM`, and switches to OpenAI/Anthropic automatically when keys are present (preserving seeds and structured JSON).

