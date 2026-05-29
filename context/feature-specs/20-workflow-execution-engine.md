# 20-workflow-execution-engine.md

Build the workflow execution engine.

The execution engine is responsible for progressing workflow runs.

## Design

Workflow definition:

Send Email

↓

Wait 3 Days

↓

Reply?

├─ Yes → Demo Call
└─ No → Follow Up

The engine should execute one step at a time.

Each recipient has its own workflow run.

## Implementation

Create:

services/

workflow_execution_service.py

Create:

WorkflowRun model

Fields:

- workflow_id
- recipient_id
- current_step
- status
- next_execution_at

Responsibilities:

- execute current step
- determine next step
- schedule future execution
- update workflow run

Support:

- send_email
- wait
- condition

No queue integration yet.

Service only.

## Check When Done

- Workflow steps execute correctly
- Step transitions work
- Conditions work
- State persists
- No type errors