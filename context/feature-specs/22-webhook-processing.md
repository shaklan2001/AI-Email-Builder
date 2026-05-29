# 22-webhook-processing.md

Process Resend webhook events.

The workflow engine must react to recipient actions.

## Design

Supported events:

- delivered
- opened
- clicked
- replied
- bounced

Webhook events drive workflow conditions.

## Implementation

Create:

POST /api/v1/webhooks/resend

Validate webhook signature.

Persist webhook events.

Update workflow run state.

Examples:

reply received

↓

condition node evaluates true

↓

yes branch executes

Store:

- event type
- timestamp
- recipient
- workflow

Prevent duplicate processing.

## Check When Done

- Webhooks received
- Signature validated
- Events stored
- Workflow updates correctly
- No duplicate processing