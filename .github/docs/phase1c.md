# Phase 1c — Next Doable Step (Magazine‑Writer Focus)

## Objective
Ship a working “mag‑writer” path that starts from unstructured notes, turns them into controllable structure, and produces a braided outline + scene drafts with fact flags — while keeping **`docs/notes.md` human‑owned (agents read‑only after seeding)**.

## Scope (now)
- Intake unstructured text → seed **Notes**, **Codex** (claims/sources/people/places), and **StoryState**.
- Planner → Draft → Fact → Revision minimal loop, **reading** from Notes/Codex; nothing writes back to Notes.
- Beat targets enforced; word band visible; inline fact flags preserved.
- Export: `story_output.json` + `exports/story_v2.md` (with beat headers).

## Inputs & Controls
- **Unstructured intake**: `docs/notes.md` (author freeform). Agents may add a one‑time *seed comment block* at the very top on import; then file becomes read‑only to agents.
- **Structured controls** (in JSON): venue, braid pattern, POV, beat quotas, grit/voice sliders, profanity mask mode (raw|masked|clean).

## Artifacts & Contracts
- **Notes (human‑owned):** `docs/notes.md` → agents: read‑only after initial seed.
- **Codex (nonfiction entities):** `docs/codex/*.md` (human readable) + `data/codex.json` (machine). Entities: `Claim{id, text, status}`, `Source{id, kind, link|quote}`, `Person{id, role}`, `Place{id, geo?}`.
- **Scene cards:** `{id, purpose, target_words, constraints{POV, motifs, voice}, locks{beats}}`.
- **Truth layer:** `claim_graph` in state references Codex IDs; revision never deletes claims.

## Agent Behavior (1c)
- **Planner** reads Notes + Codex → proposes braid & beats (JSON only). 
- **Draft** writes per‑beat prose; shows inline flags; respects mask mode.
- **Fact** links spans → `Claim{...} -> Source{...}`; appends to `claim_graph` (not Notes).
- **Revision** applies scoped rewrites; cannot alter Notes/Codex.

## Repo Changes
- `docs/notes.md` (seeded once, then agent‑read‑only)
- `docs/codex/` templates: `claims.md`, `sources.md`, `people.md`, `places.md`
- `data/codex.json` (synced from templates on import)
- `src/storygraph/codex.py` (loader/ids; maps md → json; exposes read API)
- `src/storygraph/persistence.py` (save `exports/story_v2.md`, keep beat headers)
- `prompts/` tighten JSON‑only returns; preserve `[vernacular]` markup

## Acceptance Criteria
- Run from only `docs/notes.md` + a few pasted links → get: outline (with braid), scene cards with targets, per‑scene drafts, fact flags, and `story_v2.md` with `### BEAT:` headers.
- `docs/notes.md` remains unchanged after seed step; agents read‑only.
- `claim_graph` references valid Codex IDs; no orphan claims.
- Word band + per‑beat tolerance visible in `metrics`.

## Langflow
- Defer full canvas to Phase 2. In 1c, emit a **`/exports/flow_skeleton.json`** (nodes+edges) that can be imported later.

## Next (after 1c)
- Scene drag‑reorder UI + lock controls; codex editor pane (Phase 2).
