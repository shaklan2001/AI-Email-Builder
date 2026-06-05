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

When webhook payload includes `email_id`, call `EmailService.record_delivery_event` to update `email_messages` tracking (see `19-resend-email.md`).

On `replied` events, also run reply handling (`37-reply-handling.md`): LangGraph intent classification, `inbound_replies` insert, and lead upsert. Response includes `reply_classified`, `reply_intent`, and `lead_updated`.

## Check When Done

- Webhooks received
- Signature validated
- Events stored
- Per-message tracking updated when `email_id` present
- Workflow updates correctly
- Reply classified and lead updated on `replied`
- No duplicate processing