---
description: "Generate or refine a single scene draft."
mode: "agent"
model: "gpt-5"
tools: ["read_file", "create_file", "edit_file"]
---

# Scene Draft Prompt

Context:
- Access outline and beat-level details using #file:/docs/phase0.md.
- Use StoryState fields as defined in #file:/docs/phase1.md.

Task:
- Generate or revise a **single scene**.
- Follow beat purpose, target_words, motifs, and voice style.
- Apply grit metrics and craft-pillar checklists.
- Produce **structured JSON** with fields:
  - `scene_id`
  - `text`
  - `flags` (fact, cliché, passive, overabstract)

Rules:
- Do NOT enforce global story quality gates.
- Preserve vernacular tags `<vernacular ...>`.
- Keep scope limited to the requested scene.
- Save outputs under `drafts/` or return JSON directly.
