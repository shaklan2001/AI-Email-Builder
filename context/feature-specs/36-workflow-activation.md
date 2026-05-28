# 36-workflow-activation.md

Move workflow from draft to active and start per-recipient execution.

Builds on queue wiring in `21-celery-redis-queue.md`. After activate, the **execution engine** (`20-workflow-execution-engine.md`) runs steps via Celery.

Requires approval from `35-workflow-review-stage.md`.

## Purpose

Activate an approved workflow: snapshot definition, persist status, create execution records, enqueue workers.

## Flow position

```
… → Review approved (35) → Activation (this spec) → Celery execution (21 / 20)
```

## Design

On `POST /api/v1/workflows/{workflowId}/activate`:

1. Validate workflow exists, status is `draft` or `awaiting_activation`, review approved, steps + recipients present.
2. Resolve recipients from `workflow_definition` or conversation `recipients`; upsert definition if merged.
3. **Create workflow version** — immutable snapshot in `workflow_versions` (incrementing `version`).
4. **Update workflow** — `status: active`, `activated_at`, `active_version`.
5. **Create execution record** per recipient in `executions` (`lead_id` = email, `current_step_id`, `workflow_version`).
6. **Create workflow run** per recipient in `workflow_runs` (execution engine).
7. **Enqueue** `execute_workflow_step_task` per run on `workflow_queue`.

## Status transition

```
draft | awaiting_activation  →  active
```

## API response

`ActivateWorkflowData`: `workflowId`, `status`, `activeVersion`, `activatedAt`, `executionsCreated`, `runsQueued`, `message`.

`GET /api/v1/workflows/{id}` includes `activeVersion`, `activatedAt` when set.

## Implementation

**Services**

- `backend/app/services/workflow_activation_service.py` — orchestration
- `backend/app/services/workflow_version_service.py` — Beanie `WorkflowVersion` snapshot
- `backend/app/repositories/execution_repository.py` — `executions` collection
- `backend/app/repositories/workflow_repository.py` — `activate()` sets timestamp + version

**API**

- `backend/app/api/workflows.py` — `POST /{workflow_id}/activate`

**Indexes**

- `executions` indexes in `backend/app/core/database.py`

**Frontend**

- `frontend/src/services/workflow.service.ts` — `activateWorkflow()`
- **Activate Workflow** button when `activationAllowed` (builder + review page)

**Worker**

- `cd backend && uv run celery -A app.workers.celery_app worker -l info -Q workflow_queue,email_queue,retry_queue`

**Tests**

- `backend/tests/test_activation_flow.py`
- `backend/tests/test_celery_queue.py` — activation enqueue

## Check When Done

- Activation works end-to-end (API returns `active`)
- Workflow version row created in `workflow_versions`
- `activated_at` and `active_version` stored on workflow document
- Execution record created per recipient (`executions` + `workflow_runs`)
- Celery tasks enqueued per run
- Activation blocked without review approval
- Recipients required (definition or conversation state)
- No type errors
