# 15-workflow-generation-agent.md

Generate workflow structures from the collected campaign information.

The goal is to convert conversation state into a workflow definition.

Do not generate email content yet.

Do not send emails yet.

## Design

Once sufficient information is collected:

- Business Goal
- Product
- Audience
- CTA

the AI should generate a workflow.

Workflow Types Supported:

- Linear
- Conditional
- Multi-Level Conditional

Workflow should be represented as structured JSON.

The frontend workflow preview should consume this structure.

## Implementation

Create:

agents/

workflow_agent.py

Responsibilities:

- Analyze campaign state
- Determine workflow structure
- Generate workflow definition

Output shape: `{ "steps": [] }` with generation node types:

- `send_email`
- `wait` (uses `value` + `unit` from `follow_up_delay` when present)
- `reply_condition`
- `interested_branch` / `no_reply_branch`

`backend/app/services/workflow_structure.py` — `normalize_for_execution()` maps branches to engine types (`condition`, etc.).

Follow-up timing comes from user input (hours/days/weeks), not hardcoded days.

Example:

```json
{
  "steps": [
    { "id": "step_1", "type": "send_email", "name": "Initial Outreach" },
    { "id": "step_2", "type": "wait", "value": 3, "unit": "days" },
    { "id": "step_3", "type": "reply_condition", "condition": "reply_received" },
    { "id": "step_4", "type": "interested_branch", "branch": "yes" },
    { "id": "step_5", "type": "no_reply_branch", "branch": "no", "name": "Follow Up" }
  ]
}
```

Update LangGraph:

After required campaign information is collected:

Generate Workflow Node

Return workflow structure.

Expose workflow structure through API.

Update frontend workflow preview using API response.

**Persistence**

- Workflow saved to MongoDB (`workflows.workflow_definition` + conversation state) via `persistence.py`

**Tests**

- `backend/tests/test_workflow_generation.py`

**Next in pipeline**

- Email generation: `16-email-generation-agent.md`
- Review: `35-workflow-review-stage.md`

## Check When Done

- Workflow generation works
- Workflow JSON is valid (`{ steps: [] }`)
- Saved in MongoDB; preview updates from API
- LangGraph state contains workflow
- Regenerate path clears and rebuilds when requested from review
- No hardcoded workflow templates
- No type errors