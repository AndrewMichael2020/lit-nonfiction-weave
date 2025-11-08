# Copilot Project Context — Lit-Nonfiction Weave

## Current Status
- Phase 1a complete (scaffold + LangGraph stubs + notebooks skeleton).
- Phase 1b in progress (implement real agents + validators + research + deterministic seeding).

## What Copilot Should Know
- Never modify `docs/phase0.md` or `docs/phase1.md`.
- Work happens under: `src/`, `notebooks/`, `drafts/`, `docs/changes/`.

## Current Work Targets (Phase 1b)
1. Implement real DraftAgent using Phase-0 prompt + structured schema.
2. Replace Planner stub with real outline generator.
3. Add ResearchAgent placeholder (Gemini-ready schema).
4. Add beat-level and story-level word-band validators.
5. Integrate agents in router and run `01_minimal_path.ipynb` end-to-end.

## Next Milestone
- Complete DraftAgent → first real story draft generation.

