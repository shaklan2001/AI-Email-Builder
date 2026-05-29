# 18-mongodb-persistence.md

Persist workflows and conversations in MongoDB.

## Design

Workflows should survive server restarts.

Conversation history should be stored.

Workflow definitions should be stored.

Generated emails should be stored.

## Implementation

Connect MongoDB.

Implement repositories:

- WorkflowRepository
- ConversationRepository

Persist:

- Campaign State
- Workflow Definition
- Generated Emails
- User Edits

Replace in-memory state.

## Check When Done

- [x] Data persists
- [x] Reload restores workflow
- [x] Conversation history available
- [x] No type errors

## Completed Implementation

### Files added

| File | Purpose |
|---|---|
| `backend/app/core/database.py` | Motor client, startup indexes, `connect_db` / `close_db` / `get_database` |
| `backend/app/repositories/conversation_repository.py` | `conversations` collection — campaign state, messages, workflow (incl. emails + user edits) |
| `backend/app/repositories/workflow_repository.py` | `workflows` collection — metadata + `workflow_definition` |
| `backend/app/services/persistence.py` | Dual-write helper: conversation state + workflow definition sync |

### Files updated

| File | Change |
|---|---|
| `backend/app/core/config.py` | `MONGODB_URL`, `MONGODB_DB_NAME` settings |
| `backend/app/main.py` | FastAPI lifespan connects/disconnects MongoDB on startup |
| `backend/app/services/chat_service.py` | Loads/saves via repositories (replaces in-memory store) |
| `backend/app/services/workflow_email_service.py` | Async load/save via repositories |
| `backend/app/api/workflows.py` | `POST`/`GET` workflow use `WorkflowRepository` |

### Files removed

| File | Reason |
|---|---|
| `backend/app/services/conversation_store.py` | Replaced by MongoDB persistence |

### Collections

- **`conversations`** — keyed by `(user_id, workflow_id)`; stores `messages`, campaign fields (`business_goal`, `product_info`, `audience`, `tone`, `cta`), and embedded `workflow` (steps with generated emails and user edits).
- **`workflows`** — keyed by `_id` = workflow id string; stores `name`, `status`, `workflow_definition`, timestamps.

Indexes created at startup per `docs/MongoDB_Index_Strategy.md` (conversations + workflows only).

### Env vars

```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=email_workflow_builder
```

### Verify locally

1. Start MongoDB (`mongod` or Docker).
2. Restart backend (`uv run uvicorn app.main:app --reload --port 8000`).
3. Create workflow → chat → edit email → restart server → chat/email edits still present.
