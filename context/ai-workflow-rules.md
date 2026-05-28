# AI Workflow Rules

## Approach

Spec-driven incremental build. Context files define what and how; `docs/` holds full contracts. Do not invent behavior not in specs.

When in doubt, read `docs/LLD_AI_Email_Workflow_Builder.md` and `docs/Sequence_Diagrams_AI_Email_Workflow_Builder.md` before coding.

## Build order — backend (`backend/`, uv)

```
1.  pyproject.toml + uv sync
2.  app/core/config.py, database.py, security.py
3.  app/models/
4.  app/repositories/
5.  app/providers/
6.  app/langgraph/state.py → agents/ → graph.py
7.  app/services/
8.  app/workers/
9.  app/api/ → main.py
```

## Build order — frontend (`frontend/`)

```
1.  Vite + React + MUI theme + TanStack QueryProvider
2.  api/client.ts + queryKeys + Clerk token bridge
3.  Protected routes + AppShell (MUI)
4.  Pages per docs/Frontend_Screen_Flow.md
5.  One hook per API endpoint; wire MUI components
```

## Scoping rules

- One layer or one feature at a time.
- Do not mix unrelated backend + frontend in one step.
- Do not implement Not-MVP features.

## When to split work

Split if touching: service + worker, API + new agent, multiple collections' schemas, or undefined behavior.

## Protected files (do not edit unless user asks)

- `docs/*.md` — design source of truth
- `ARCHITECTURE_DECISIONS.md` — unless adding a new ADR

## Keeping docs in sync

| Change type | Update |
|---|---|
| Architecture / invariant | `context/architecture.md` |
| UI / routes / hooks | `context/ui-context.md` + `docs/Frontend_Screen_Flow.md` |
| Standards | `context/code-standards.md` |
| Scope | `context/project-overview.md` + `docs/MVP_Scope.md` |
| Progress | `context/progress-tracker.md` |
| Full design detail | `docs/` directly |

## Before the next unit

1. Current unit works in scope.
2. No `architecture.md` invariant violated.
3. `progress-tracker.md` updated.
4. MVP scope respected.
