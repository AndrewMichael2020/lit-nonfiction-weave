---
description: "Architecture guide for the lit-nf-stories project."
mode: "agent"
model: "gpt-5"
tools: ["read_file", "search/codebase", "create_file", "edit_file"]
---

# Architecture Prompt

Use the project specifications stored in:
- #file:/docs/phase0.md
- #file:/docs/phase1.md

**Do not modify those files.**  
You may create or modify files under `src/`, `tests/`, `notebooks/`, and `docs/changes/`.

Your responsibilities:
- Maintain the StoryState schema.
- Maintain agent structure: Planner → Draft → Fact → Revision (+ Research).
- Enforce output schemas from Phase 0.
- Use deterministic seeds.
- Keep all generated artifacts reproducible.

When writing code:
- Keep functions small and explicit.
- Use typed Pydantic models.
- Never remove vernacular tags.
