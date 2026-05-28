# Architecture Context

## Stack

| Layer | Technology | Role |
|---|---|---|
| Frontend | React 19 + TypeScript + Vite | UI — chat, previews, analytics |
| Frontend UI | MUI (Material UI) v6 | Components, theme, layout — sole UI library |
| Frontend Data | TanStack Query v5 | Server state, mutations, cache invalidation |
| Frontend Auth | Clerk React SDK | Session, JWT on API requests |
| Backend | Python 3.12+ (3.14 target) | API and workers |
| Package Manager | **uv** | `backend/pyproject.toml` + `uv.lock` — no pip/poetry |
| API | FastAPI (async) | Gateway for all client requests |
| AI | LangGraph + LangChain | Multi-agent campaign builder |
| LLM | Groq (via `LLMProvider`) | Swappable provider |
| Database | MongoDB + Motor | All domain persistence |
| Queue | Redis | Celery broker |
| Workers | Celery | Email send, workflow steps, webhooks |
| Email | Resend (via `EmailProvider`) | Send + webhooks |
| Monitoring | LangSmith | Agent tracing |

## Monorepo layout

```
frontend/          → React app (MUI + TanStack Query)
backend/app/       → FastAPI, services, agents, workers
context/           → Cursor agent context (this folder)
docs/              → Canonical design documents
```

## System boundaries

- `backend/app/api/` — Thin FastAPI handlers. Auth, parse, delegate, return.
- `backend/app/services/` — Business logic per domain.
- `backend/app/repositories/` — MongoDB CRUD only. One file per collection.
- `backend/app/agents/` — One LangGraph agent per file.
- `backend/app/langgraph/` — `graph.py`, `state.py`, `nodes.py` only.
- `backend/app/workers/` — Celery tasks only.
- `backend/app/providers/` — Abstract LLM + email; concrete Groq + Resend injected.
- `frontend/src/api/` — `client.ts`, `queryKeys.ts`, hooks — all HTTP here.
- `frontend/src/pages/` — Route screens; use MUI + TanStack hooks only.

## Storage model

- **MongoDB:** users, conversations, workflows, email_templates, recipients, workflow_runs, analytics, webhook_events.
- **Redis:** Celery queue and delayed `eta` jobs only — no domain data.

## Auth and access

- Clerk JWT on every protected API request (`Authorization: Bearer`).
- Every workflow-owned query includes `user_id` + document id.

## LangGraph stages

```
CAMPAIGN_DISCOVERY → AUDIENCE_DISCOVERY → CONTENT_DISCOVERY →
ASSET_COLLECTION → RECIPIENT_COLLECTION → WORKFLOW_GENERATION →
EMAIL_GENERATION → REVIEW → APPROVAL → COMPLETE
```

See `docs/LangGraph_State_Diagram.md`.

## Workflow step types (MVP)

| Type | Purpose |
|---|---|
| `send_email` | Send template for step |
| `wait` | Celery `eta` delay (days) |
| `condition` | Branch on `reply_received` |
| `end` | Complete run |

## Invariants

1. Route handlers contain no business logic.
2. No `time.sleep` or polling — wait steps use Celery `eta`.
3. Services use `LLMProvider` / `EmailProvider` abstractions only.
4. All workflow queries filter by `user_id`.
5. Email templates versioned — engine uses latest `version` per step.
6. Webhooks idempotent via `event_id` / `processed` flag.
7. MVP scope fixed — see `docs/MVP_Scope.md`.
8. Frontend: no raw `fetch` in pages; MUI only for UI.

## Related docs

- Indexes: `docs/MongoDB_Index_Strategy.md`
- ADRs: `ARCHITECTURE_DECISIONS.md`
- LLD detail: `docs/LLD_AI_Email_Workflow_Builder.md`
