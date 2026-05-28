# Code Standards

## General

- One concern per module. One service per domain. One agent per LangGraph concern. One repository per collection.
- Fix root causes — no workaround flags.
- Never implement "Out of Scope" items in `context/project-overview.md` or `docs/MVP_Scope.md`.
- **Do not write application code** unless the user explicitly requests implementation.

## Backend — uv

- All Python deps in `backend/pyproject.toml`. Lock with `uv.lock`.
- Install: `cd backend && uv sync`
- Run: `uv run uvicorn app.main:app --reload`
- Add dep: `uv add <package>` — never `pip install` in this repo.

## Python / FastAPI

- Async throughout route handlers and services.
- Type-annotate all signatures. `CampaignState` TypedDict for LangGraph. Pydantic for API bodies.
- Config via `pydantic-settings` in `core/config.py` only.
- Thin routes: `Depends(get_current_user)` → one service call → response model.
- Ownership: every workflow query includes `user_id`.

## LangGraph / Celery / MongoDB

- State fields only in `langgraph/state.py`. Routing only in `langgraph/nodes.py`. Graph wiring only in `graph.py`.
- Celery: `bind=True`, explicit retries; wait steps use `eta`, never multi-day `sleep`.
- Motor async only. Repositories only touch DB. Analytics updates use `$inc`.
- Indexes at startup — see `docs/MongoDB_Index_Strategy.md`.

## Providers

- Services depend on `LLMProvider` and `EmailProvider` ABCs. Inject Groq/Resend via FastAPI `Depends`.

## Webhooks

- Verify Resend HMAC before processing. Enqueue Celery task; return 200 immediately. Idempotent on `event_id`.

## Frontend — React + MUI + TanStack Query

- TypeScript strict mode.
- **No raw `fetch` in `pages/` or feature components.** Use `src/api/client.ts` + hooks in `src/api/hooks/`.
- **MUI only** for UI. Theme in `src/theme/muiTheme.ts`.
- Query keys centralized in `src/api/queryKeys.ts`.
- Clerk token attached in `apiClient` via `setAuthTokenGetter`.
- Invalidate queries after mutations (activate, upload, chat when workflow state changes).

## File organization

| Path | Contents |
|---|---|
| `backend/app/api/` | Route handlers |
| `backend/app/services/` | Business logic |
| `backend/app/repositories/` | MongoDB CRUD |
| `backend/app/agents/` | LangGraph agents |
| `backend/app/langgraph/` | Graph, state, nodes |
| `backend/app/workers/` | Celery tasks |
| `backend/app/providers/` | LLM + email providers |
| `frontend/src/api/` | client, queryKeys, hooks |
| `frontend/src/pages/` | Route screens |
| `frontend/src/components/` | Shared MUI compositions |
