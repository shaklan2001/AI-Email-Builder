# 21-celery-redis-queue.md

Integrate Redis and Celery.

Workflow execution must happen in background workers.

## Design

Workflow execution should never block API requests.

Use:

FastAPI
↓
Redis
↓
Celery Worker

Architecture:

Activate Workflow
↓
Queue Job
↓
Worker Executes

## Implementation

Add:

Redis

Celery

Create queues:

- workflow_queue
- email_queue
- retry_queue

Create tasks:

- send_email_task
- execute_workflow_step_task
- resume_workflow_task

Workflow activation should enqueue jobs.

Workers should process execution.

## Check When Done

- Redis connected
- Celery running
- Jobs enqueue correctly
- Workers process jobs
- No type errors