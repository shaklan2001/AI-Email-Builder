# Architecture Decision Records (ADR)

# AI-Driven Email Workflow Builder

This document captures **why** key technology choices were made. Reference during implementation to avoid scope creep and accidental rewrites.

---

## ADR-001: MongoDB for primary data store

**Status:** Accepted  
**Date:** 2026-06-03

### Context

Workflow definitions include variable step types (`send_email`, `wait`, `condition`, `end`) with nested `config` objects. Campaign and conversation state evolve over many chat turns.

### Decision

Use **MongoDB** with the Motor async driver for all application persistence.

### Rationale

- Document model fits dynamic workflow graphs without rigid relational migrations per step type.
- Embedding `campaign_state` on `conversations` reduces joins during chat turns.
- Horizontal scaling path via sharding on `user_id` is documented in LLD for future growth.

### Consequences

- Index strategy is mandatory (see `docs/MongoDB_Index_Strategy.md`).
- No SQL transactions across services; use application-level consistency for activation (create `workflow_runs` then enqueue).

### Alternatives considered

- **PostgreSQL + JSONB:** Strong consistency but heavier schema churn for MVP.
- **Firestore:** Vendor lock-in; team stack is Python + Mongo.

---

## ADR-002: LangGraph for AI orchestration

**Status:** Accepted  
**Date:** 2026-06-03

### Context

Campaign building is a **multi-step, stateful conversation** across discovery, workflow design, copywriting, and review.

### Decision

Use **LangGraph** (`StateGraph` + supervisor routing) with discrete agent nodes.

### Rationale

- Explicit stages (`CAMPAIGN_DISCOVERY` → `COMPLETE`) map to nodes and conditional edges.
- Checkpoint-friendly state (`CampaignState`) persists to MongoDB between HTTP requests.
- LangSmith integrates for tracing without custom instrumentation.

### Consequences

- Graph must **not** send emails or call Celery — see ADR-003 separation.
- `current_stage` must be persisted on every chat turn.

### Alternatives considered

- **Single monolithic prompt:** Harder to debug and extend per agent.
- **Manual if/else chains:** Duplicates LangGraph routing logic.

---

## ADR-003: Redis + Celery for workflow execution

**Status:** Accepted  
**Date:** 2026-06-03

### Context

Workflows include **wait steps** (days) and high-volume email sends. HTTP requests cannot hold process state for days.

### Decision

Use **Redis** as Celery broker and **Celery workers** for `execute_workflow_step_task`, `send_email_task`, and delayed `resume_workflow_task` via `eta`.

### Rationale

- Workers query `workflow_runs` by `next_execution_at` + `status` (indexed).
- No polling loops or `sleep()` in application code.
- Workers scale horizontally independent of FastAPI replicas.

### Consequences

- Requires `REDIS_URL` and worker deployment alongside API.
- Idempotent webhook processing required (ADR-004).

### Alternatives considered

- **In-process asyncio timers:** Lost on deploy/restart.
- **Kafka (MVP):** Deferred to future scale path in HLD.

---

## ADR-004: Resend for email delivery and webhooks

**Status:** Accepted  
**Date:** 2026-06-03

### Context

MVP needs send, delivery/open/click tracking, and **reply detection** for conditional workflow branches.

### Decision

Use **Resend** behind an `EmailProvider` abstraction with webhook ingestion at `POST /api/webhooks/resend`.

### Rationale

- Single provider covers transactional send + event webhooks.
- HMAC signature verification supported.
- Keeps MVP integration surface small.

### Consequences

- Store raw events in `webhook_events` with dedup index.
- Map `resend_message_id` → `workflow_run` for analytics updates.

### Alternatives considered

- **SendGrid / SES:** Comparable; Resend chosen for DX and webhook clarity in assignment scope.

---

## ADR-005: Provider pattern for LLM and email

**Status:** Accepted  
**Date:** 2026-06-03

### Context

Assignment requires swappable LLM; product may change email vendor later.

### Decision

Define abstract `LLMProvider` and `EmailProvider` in `app/providers/`. Inject **Groq** and **Resend** implementations via FastAPI dependencies.

### Rationale

- Services depend on interfaces, not concrete SDKs.
- Enables testing with mocks.
- Future: Claude/OpenAI/Gemini without rewriting agents.

### Consequences

- **Never** import `GroqProvider` / `ResendProvider` directly inside `services/` or `agents/`.
- Configuration via environment variables only.

### Alternatives considered

- **Direct SDK calls everywhere:** Faster initially, expensive to swap.

---

## ADR-006: Clerk for authentication

**Status:** Accepted  
**Date:** 2026-06-03

### Context

MVP needs secure login without building auth from scratch.

### Decision

**Clerk** on frontend (React SDK) and JWT verification on FastAPI (`CLERK_PEM_PUBLIC_KEY` or Clerk JWKS).

### Rationale

- JWT-based stateless API auth.
- Sync `clerk_user_id` → `users` collection.

### Consequences

- Every protected route uses `Depends(get_current_user)`.
- All workflow queries filter by `user_id` (authorization).

---

## ADR-007: Separate workflow creation from execution

**Status:** Accepted  
**Date:** 2026-06-03

### Context

AI workloads (LLM latency, token cost) differ from execution workloads (email throughput, retries).

### Decision

**LangGraph / AIService** creates definitions and templates. **WorkflowService + Celery** executes after explicit user **APPROVAL** (`activate`).

### Rationale

- Prevents accidental email send during chat.
- Clear lifecycle: `draft` → `awaiting_approval` → `active`.

### Consequences

- Activation creates one `workflow_run` per recipient.
- Pause sets `workflows.status = paused`; workers check status before each step.

---

## ADR-008: MVP scope boundary (non-ADR feature list)

**Status:** Accepted  
**Date:** 2026-06-03

### Decision

Implement only features listed in `docs/MVP_Scope.md`. Defer multi-tenant, A/B tests, CRM, per-recipient AI emails, custom domains, SMS/WhatsApp.

### Rationale

Assignment success depends on **end-to-end demo**, not feature breadth.

### Consequences

- Cursor and contributors must reject PRs that add future-scope modules without explicit approval.

---

## ADR-009: TanStack Query for frontend API state

**Status:** Accepted  
**Date:** 2026-06-03

### Context

Multiple screens share workflow and analytics data. Manual `fetch` + `useEffect` causes duplicate requests, stale UI, and inconsistent loading/error handling.

### Decision

Use **@tanstack/react-query** for all REST calls to FastAPI.

### Rationale

- Built-in cache, deduplication, and background refetch (analytics polling).
- `useMutation` + `invalidateQueries` fits activate/upload/chat flows.
- Keeps pages thin; hooks live in `frontend/src/api/hooks/`.

### Consequences

- No server data in Zustand/Redux for MVP.
- Single `api/client.ts` attaches Clerk Bearer token.

### Alternatives considered

- **SWR:** Comparable; TanStack Query chosen for mutation/invalidation ergonomics.
- **Raw fetch in components:** Rejected — duplicates loading/error logic.

---

## ADR-010: MUI for UI components

**Status:** Accepted  
**Date:** 2026-06-03

### Context

MVP needs consistent layout, forms, tables, and dialogs quickly without custom CSS systems.

### Decision

Use **@mui/material** (+ `@emotion/react`) as the sole component library.

### Rationale

- Production-ready accessibility and theming.
- Maps cleanly to dashboard, builder split view, modals, analytics cards.
- One design language — no mixing Tailwind + MUI.

### Consequences

- Custom styling via MUI `sx` prop and `theme/muiTheme.ts`.
- Do not add shadcn, Chakra, or Ant Design.

### Alternatives considered

- **Tailwind + headless:** More assembly time for assignment deadline.

---

## ADR-011: uv for Python dependency management

**Status:** Accepted  
**Date:** 2026-06-03

### Context

Backend is FastAPI + Celery + LangGraph with many dependencies. Reproducible installs matter for CI and teammates.

### Decision

Use **uv** with `backend/pyproject.toml` and committed `uv.lock`.

### Rationale

- Fast installs and lockfile discipline.
- `uv run` replaces manual venv activation for uvicorn/celery/pytest.

### Consequences

- Add packages: `uv add fastapi`, not `pip install`.
- CI: `uv sync --frozen`.
- Backend code lives under `backend/app/`.

### Alternatives considered

- **pip + requirements.txt:** Weaker lock semantics.
- **Poetry:** Heavier; uv is faster for this stack.

---

## Document index

| Artifact | Path |
|---|---|
| Frontend flows | `docs/Frontend_Screen_Flow.md` |
| LangGraph stages | `docs/LangGraph_State_Diagram.md` |
| MongoDB indexes | `docs/MongoDB_Index_Strategy.md` |
| MVP boundary | `docs/MVP_Scope.md` |
| Environment template | `.env.example` |
| LLD implementation | `docs/LLD_AI_Email_Workflow_Builder.md` |
| Backend deps (when implemented) | `backend/pyproject.toml` |
| Frontend deps (when implemented) | `frontend/package.json` |
