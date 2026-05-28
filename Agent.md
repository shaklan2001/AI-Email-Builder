# AI Email Workflow Builder — Cursor Agent Instructions

Read this file first. Then read `context/` files **in order** before implementing or making architectural decisions.

## Read order (required)

1. `context/project-overview.md` — product definition, goals, MVP scope
2. `context/architecture.md` — stack, boundaries, invariants
3. `context/ui-context.md` — MUI theme, layout, screen flow
4. `context/code-standards.md` — Python, FastAPI, frontend, uv rules
5. `context/ai-workflow-rules.md` — build order, scoping, protected files
6. `context/progress-tracker.md` — current phase, next steps, ADRs

After each meaningful change, update `context/progress-tracker.md`.

If implementation changes architecture, scope, or standards, update the relevant `context/` file **before** continuing.

## Design docs (read-only reference)

Canonical specs live in `docs/`. Do **not** edit unless the user explicitly asks.

| File | Purpose |
|---|---|
| `docs/PRD_AI_Email_Workflow_Builder_v2.md` | Product requirements |
| `docs/HLD_AI_Email_Workflow_Builder_v2.md` | High-level architecture |
| `docs/LLD_AI_Email_Workflow_Builder.md` | Schemas, APIs, folder structure, Celery |
| `docs/Sequence_Diagrams_AI_Email_Workflow_Builder.md` | Call order and data flow |
| `docs/Frontend_Screen_Flow.md` | Routes, TanStack Query, MUI |
| `docs/LangGraph_State_Diagram.md` | Agent stages and routing |
| `docs/MongoDB_Index_Strategy.md` | Index definitions |
| `docs/MVP_Scope.md` | MVP vs not-MVP guardrails |

Also: `ARCHITECTURE_DECISIONS.md` (ADRs).

## Repo layout (when code exists)

```
/
├── Agent.md
├── context/          ← agent working memory (6 files)
├── docs/             ← design documents
├── frontend/
└── backend/
```

## Hard rules

- Implement code only when the user asks. Otherwise update `context/` or `docs/`.
- **MVP scope:** `docs/MVP_Scope.md`
- **Frontend:** MUI + TanStack Query only
- **Backend:** uv only (`uv add`, not pip)
- LangGraph builds campaigns; Celery runs after user approval only
