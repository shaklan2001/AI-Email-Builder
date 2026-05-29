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

Output Example:

{
  "steps": [
    {
      "id": "step_1",
      "type": "send_email",
      "name": "Initial Product Launch"
    },
    {
      "id": "step_2",
      "type": "wait",
      "days": 3
    },
    {
      "id": "step_3",
      "type": "condition",
      "condition": "reply_received"
    },
    {
      "id": "step_4",
      "type": "send_email",
      "name": "Follow Up"
    }
  ]
}

Update LangGraph:

After required campaign information is collected:

Generate Workflow Node

Return workflow structure.

Expose workflow structure through API.

Update frontend workflow preview using API response.

## Check When Done

- Workflow generation works
- Workflow JSON is valid
- Frontend preview updates
- LangGraph state contains workflow
- No hardcoded workflow templates
- No type errors