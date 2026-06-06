# 20-workflow-execution-engine.md

Execute active workflows step-by-step for each recipient.

Integrates with **Celery + Redis** (`21-celery-redis-queue.md`), **activation** (`36-workflow-activation.md`), and **Resend** (`19-resend-email.md`).

## Purpose

Progress `workflow_runs` through send → wait → condition → follow-up automatically after activation.

## Architecture

```
POST /api/v1/workflows/{id}/activate  (API)
        ↓
Redis (Celery broker)
        ↓
Celery worker (workflow_queue / email_queue)
        ↓
WorkflowExecutionService (execution engine)
        ↓
MongoDB workflow_runs + Resend sends
```

- **Activation** enqueues `execute_workflow_step_task` per recipient.
- **send_email** steps run on `email_queue` (isolates Resend latency).
- **Wait** steps set `next_execution_at`; Celery `resume_workflow_task` runs at `eta` (hours/days/weeks).
- **Follow-up** = `send_email` on the `no` branch after `reply_condition` evaluates false.

## Design

One step per `execute_step` call per recipient run.

Each recipient has its own `workflow_run` (`workflow_id`, `recipient_id`, `current_step`, `status`, `next_execution_at`).

Active workflows load the **frozen** definition from `workflow_versions` (`active_version` on the workflow document).

## Step types

| Type | Behavior |
|------|----------|
| `send_email` | `EmailService.send_email` → advance; if next step is `wait`, schedule wait immediately |
| `wait` | Set `status=waiting`, `next_execution_at = now + delay` |
| `condition` / `reply_condition` | Requires `condition_result` (webhook or test); routes to yes/no branch steps |
| Follow-up | `send_email` with `branch: no` after no-reply path |

Generation types (`reply_condition`, `no_reply_branch`, …) are normalized via `workflow_structure.normalize_for_execution()`.

## Wait durations

From wait step `value` + `unit`, or workflow `follow_up_delay`:

- **hours** — `timedelta(hours=value)`
- **days** — `timedelta(days=value)`
- **weeks** — `timedelta(weeks=value)`

Implemented in `follow_up_delay_to_timedelta()`; used by `_wait_timedelta()` in the execution service.

Celery `dispatch_after_step` schedules `resume_workflow_task` with `eta=next_execution_at`.

## Implementation

**Engine**

- `backend/app/services/workflow_execution_service.py` — `create_run`, `execute_step`, `process_due_runs`
- `backend/app/models/workflow_run.py`
- `backend/app/repositories/workflow_run_repository.py`

**Workers**

- `backend/app/workers/workflow_runner.py` — `run_execute_workflow_step`, `run_resume_workflow`
- `backend/app/workers/workflow_worker.py` — Celery tasks
- `backend/app/workers/email_worker.py` — send_email via engine + dispatch
- `backend/app/workers/dispatch.py` — chain execute / resume with `eta`

**Version snapshot**

- `workflow_version_service.get_definition_dict()` — used when `workflow.status == active"`

**Tests**

- `backend/tests/test_workflow_execution_service.py` — transitions, branches, full no-reply + follow-up path
- `backend/tests/test_workflow_execution_wait_durations.py` — hours / days / weeks scheduling
- `backend/tests/test_celery_queue.py` — dispatch, activation enqueue

## Run locally

```bash
# Terminal 1 — API
cd backend && uv run uvicorn app.main:app --reload

# Terminal 2 — Celery worker
cd backend && uv run celery -A app.workers.celery_app worker -l info -Q workflow_queue,email_queue,retry_queue
```

Requires Redis (`REDIS_URL`) and MongoDB. Activate workflow after review approval (spec 35).

## Check When Done

- Workflow executes automatically after activate (Celery tasks enqueued)
- `send_email` step sends via Resend and advances
- `wait` step schedules resume at correct time (hours, days, weeks)
- Follow-up `send_email` runs on no-reply branch
- Conditions route to yes/no branches
- State persists on `workflow_runs`
- Active workflows use frozen `workflow_versions` definition
- No type errors
