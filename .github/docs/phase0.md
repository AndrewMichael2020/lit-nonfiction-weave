# Phase 0 — Craft & Prompts Pack (Literary Non‑Fiction Short Stories)

Version: 0.1 • Target length per story: 3,000–7,500 words • Seeds: default `SEED=137` unless specified.

---

## A) Structure Templates (finalized)
Templates default to **scenes/sections** (no chapters unless toggled). Each template includes a JSON outline schema, beat purposes, and word‑count guidance. Replace placeholders in `{curly}`.

### 1) **Braided (A/B/C strands)**
**Use when**: personal narrative + reported context + backstory need to interleave.

**Beats** (repeatable cycle):
- **A: Live Scene** — present‑tense moment with concrete stakes.
- **B: Backstory** — past event that illuminates A’s tension.
- **C: Context** — reported facts, quotes, or cultural lens.
- **Hinge** — recontextualizes A with B/C, raises the central question.
- **Resolution/Turn** — change in understanding; earned reflection.

**Word split (target 4,500 words example)**: A 40% • B 25% • C 20% • Hinge 5% • Resolution 10%.

**Outline JSON schema**:
```json
{
  "template": "braided",
  "strands": ["A_live", "B_backstory", "C_context"],
  "beats": [
    {"id": "s1", "strand": "A_live", "purpose": "Introduce immediate tension and scene stakes", "target_words": 500},
    {"id": "s2", "strand": "B_backstory", "purpose": "Reveal formative event that complicates s1", "target_words": 400},
    {"id": "s3", "strand": "C_context", "purpose": "Report facts/quotes that refract s1", "target_words": 350},
    {"id": "s4", "strand": "A_live", "purpose": "Escalate conflict with specific obstacle", "target_words": 600},
    {"id": "s5", "strand": "B_backstory", "purpose": "Cost/choice in the past echoing present", "target_words": 400},
    {"id": "s6", "strand": "C_context", "purpose": "Counter‑evidence or alternative lens", "target_words": 350},
    {"id": "hinge", "strand": "A_live", "purpose": "Reframe: insight crystallizes via concrete beat", "target_words": 200},
    {"id": "resolution", "strand": "A_live", "purpose": "Earned reflection grounded in scene detail", "target_words": 400}
  ]
}
```

### 2) **Dual Timeline (Now/Then → Hinge)**
**Use when**: a present quest depends on a past thread.

**Beats**: NOW‑1 → THEN‑1 → NOW‑2 → THEN‑2 → Hinge → NOW‑3 → Resolution.

**Word split (4,500 example)**: NOW 50% • THEN 30% • Hinge 5% • Resolution 15%.

**Outline JSON schema**:
```json
{
  "template": "dual_timeline",
  "timelines": ["now", "then"],
  "beats": [
    {"id": "n1", "timeline": "now", "purpose": "Concrete problem in motion", "target_words": 600},
    {"id": "t1", "timeline": "then", "purpose": "Origin that sets stakes", "target_words": 500},
    {"id": "n2", "timeline": "now", "purpose": "Escalation + obstacle", "target_words": 600},
    {"id": "t2", "timeline": "then", "purpose": "Reveals hidden cost", "target_words": 450},
    {"id": "hinge", "timeline": "now", "purpose": "Collision of timelines", "target_words": 250},
    {"id": "n3", "timeline": "now", "purpose": "Choice under pressure", "target_words": 550},
    {"id": "resolution", "timeline": "now", "purpose": "Aftermath + earned reflection", "target_words": 550}
  ]
}
```

### 3) **Mosaic (numbered fragments)**
**Use when**: resonance emerges from juxtaposed micro‑sections.

**Beats**: 9–21 fragments of 80–250 words each; recurring **motifs** bind them.

**Outline JSON schema**:
```json
{
  "template": "mosaic",
  "fragments": [
    {"id": "f1", "purpose": "Anchor image", "motifs": ["{motif1}"]},
    {"id": "f2", "purpose": "Counterpoint voice/quote", "motifs": ["{motif2}"]},
    {"id": "f3", "purpose": "Memory shard reframing f1", "motifs": ["{motif1}"]}
  ],
  "target_fragment_words": [120, 180]
}
```

### 4) **Quest (reported feature with personal stakes)**
**Use when**: external objective drives arc; reporting + interiority.

**Beats**: Hook → Setup → First Obstacle → Midpoint reversal → Second Obstacle → Climax choice → Aftermath/Insight.

**Outline JSON schema**:
```json
{
  "template": "quest",
  "beats": [
    {"id": "hook", "purpose": "Problem stated via vivid event", "target_words": 500},
    {"id": "setup", "purpose": "Who/where/why now; promise to the reader", "target_words": 600},
    {"id": "ob1", "purpose": "External block", "target_words": 500},
    {"id": "mid", "purpose": "Reversal or discovery", "target_words": 600},
    {"id": "ob2", "purpose": "Costly attempt", "target_words": 500},
    {"id": "choice", "purpose": "Decision under pressure", "target_words": 500},
    {"id": "aftermath", "purpose": "Consequences + earned reflection", "target_words": 500}
  ]
}
```

---

## B) Grit Metrics (scene‑level)
Each scene records counters; pass/fail thresholds are enforced in Draft Audit.

- **ObstacleCount ≥ 1** — there must be a specific friction point.
- **ChoiceDeclared ∈ {true,false}** — a decision or trade‑off is explicit.
- **CostMentioned ∈ {true,false}** — time, money, status, relationship, or identity cost.
- **ConcreteDetailDensity ≥ 0.25** — proportion of sentences containing tactile specifics (objects, textures, place names, measurements).
- **SelfImplication ∈ {none, light, explicit}** — narrator’s role in outcome.
- **CounterEvidenceUsed ∈ {true,false}** — for reported claims, at least one counter lens appears across the story.

**Formulae** (per story):
- `GritScore = 0.3*ObstacleRate + 0.2*ChoiceRate + 0.2*CostRate + 0.2*ConcreteDetailDensity + 0.1*SelfImplicationLevel`
- Minimum acceptable `GritScore ≥ 0.65`.

---

## C) Craft‑Pillar Checklists
Attach to each **scene**; roll‑up is computed for the whole story. Using plain bullets with Unicode boxes so they render in all views.

### 1) Opening strength
- ☑ Concrete image appears within first 2–3 sentences
- ☑ Implied question or tension is present
- ☑ Specific who/where anchor is stated
- ☑ First paragraph avoids abstract thesis statements

### 2) Scene purpose
- ☑ Beat’s intent is explicit (conflict, reveal, reversal, link)
- ☑ Progress or pressure increases by scene end
- ☑ Exit leaves changed state or sharper question
- ☑ Scene ties to story thesis (one line)

### 3) Specificity & facts
- ☑ Proper nouns and measured details are present
- ☑ Claims link to sources or are marked as personal memory
- ☑ Counter lens considered where argumentative
- ☑ Any statistics include method context (who/when/how)

### 4) Voice & rhythm
- ☑ Filter words trimmed
- ☑ Passive ratio within tolerance
- ☑ Sentence length variance present
- ☑ Cliché detector shows ≤ 2 hits per 1,000 words

### 5) Grit
- ☑ Obstacle is present
- ☑ Choice is forced
- ☑ Cost is named (time/money/status/relationship/identity)
- ☑ Self‑implication considered
- ☑ Concrete grime/detail appears at least once

### 6) Reflection
- ☑ Insight arises from scene action, not lecture
- ☑ Metaphor grounded in concrete detail
- ☑ No unearned summarizing
- ☑ Final line carries resonance without tying a bow

**Per‑scene JSON attachable example**
```json
{
  "scene_id": "s4",
  "checklist": {
    "opening_strength": [true, true, true, false],
    "scene_purpose": [true, true, true, true],
    "specificity_facts": [true, true, false, true],
    "voice_rhythm": [true, true, true, true],
    "grit": [true, true, true, true, true],
    "reflection": [true, true, true, true]
  }
}
```

---

## D) Vernacular & Profanity Controls (immutable)
- **Lexicon file** `vernacular.json` with entries: `{ "term": "{token}", "mask": true|false, "variants": ["..."], "context": ["dialogue","interiority","quote"], "notes": "..." }`.
- **Markup**: wrap tokens as `<vernacular id="v{n}" mask="true">token</vernacular>` to survive later rewrites.
- **Render modes**: `raw` | `masked` | `clean` at export time.

---

## E) Prompt Library (with seeds)
**Conventions**: each prompt has `system`, `user`, optional `tool_instructions`, an `output_schema`, and a `SEED` default. Replace `{variables}`.

### E1) PlannerAgent — pick structure & beats
**SEED=137**
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

### E2) ResearchAgent — quotes & claim map
**SEED=173**
```
[system]
Extract verbatim quotes and claims with citations from uploaded sources. Normalize entities. Return JSON suitable for a claim graph.

[output_schema]
{"quotes": [{"id":"q1","text":"...","source_id":"...","page":n}], "claims":[{"id":"c1","sentence":"...","evidence":["q1","q2"],"status":"supported|contested|anecdotal"}]}

[user]
Topics: {topics}
Priority lens: {lens}
```

### E3) VoiceAgent — style rules
**SEED=191**
```
[system]
Infer diction rules from author sample. Produce a tone matrix, banned phrases, and cadence notes. Do not imitate specific authors; keep unique voice.

[output_schema]
{"tone": {"warmth":0-1,"irony":0-1,"restraint":0-1}, "banned_phrases":["..."], "syntax_notes":["..."], "lexicon_pref":["..."]}

[user]
Author sample (300–800 words): {sample}
Venue target: {venue}
```

### E4) DraftAgent — scene‑by‑scene generation
**SEED=223**
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

### E5) FactAgent — verification & rewrite suggestions
**SEED=251**
```
[system]
Map factual sentences to the claim graph. Propose minimal rewrites for unsupported lines.

[output_schema]
{"links":[{"span":"...","claim_id":"c1","status":"supported|needs_cite|rewrite"}], "suggestions":[{"span":"...","rewrite":"..."}]}

[user]
Scene text: {scene}
Claim graph: {graph}
```

### E6) RhythmAgent — metrics only
**SEED=277**
```
[system]
Compute sentence length histogram, passive ratio, adverb density, and cliché list matches. Do not rewrite; return numbers.

[output_schema]
{"sent_hist":[...],"passive_ratio":0-1,"adverb_density":0-1,"cliche_hits":["..."]}

[user]
Text: {text}
```

### E7) RevisionAgent — targeted rewrite
**SEED=311**
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

---

## F) Validation Rules (Draft Audit)
- Word band: 3,000–7,500; each beat within ±15% of `target_words` unless marked `intentionally_long|short`.
- Grit minimums: ObstacleCount≥1, ChoiceDeclared, CostMentioned per 2 consecutive scenes.
- Specificity: ≥25% sentences with concrete detail tokens.
- Rhythm: passive_ratio ≤ 0.25; adverb_density ≤ 0.18 unless venue preset allows.
- Facts: all claims either `supported` or flagged with suggested rewrites.

---

## G) File Layout (repo)
```
phase0/
  templates/
    braided.json
    dual_timeline.json
    mosaic.json
    quest.json
  prompts/
    planner.txt
    research.txt
    voice.txt
    draft.txt
    fact.txt
    rhythm.txt
    revision.txt
  lexicon/
    vernacular.json
  validation/
    draft_rules.json
  seeds.md
```

**seeds.md**
```
PlannerAgent SEED=137
ResearchAgent SEED=173
VoiceAgent SEED=191
DraftAgent SEED=223
FactAgent SEED=251
RhythmAgent SEED=277
RevisionAgent SEED=311
```

---

## H) Ready‑to‑commit Notes
- All prompts use explicit `output_schema` to keep results structured.
- Seeds defined; swap‑able per run for exploration but persisted in StoryState.
- Vernacular markup and lexicon prepared to prevent accidental sanitization.
- Templates finalized and JSON‑serializable.

