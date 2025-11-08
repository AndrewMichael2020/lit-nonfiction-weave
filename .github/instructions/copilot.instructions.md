# Global Copilot Instructions

- Treat every file under `docs/**` as **read-only**.  
  Do **not** edit or rewrite Phase documents directly.

- When a change to Phase 0 or Phase 1 is requested, Copilot must:
  1) Create a new markdown file under `docs/changes/`, OR  
  2) Open a Pull Request with the proposed edits — **but never modify docs in-place.**

- Always prefer **structured outputs** (JSON / YAML / Markdown tables).

- Respect seeds and deterministic behavior for all LangGraph agents.

- Maintain `<vernacular ...>` tags without alteration. Keep render modes: `raw | masked | clean`.

- For code generation, target Python 3.11 and preserve folder layout.
