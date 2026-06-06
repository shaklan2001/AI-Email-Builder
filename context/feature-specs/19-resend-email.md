# 19-resend-email.md

Integrate Resend as the email delivery provider with persisted message records and delivery tracking.

Related: `22-webhook-processing.md` (webhook events), `23-analytics.md` (workflow counters).

## Purpose

Send emails through Resend, store each outbound message, and track lifecycle events per lead.

## Design

Email sending is abstracted behind `EmailProvider` (swappable). `EmailService` orchestrates sends, persistence, and analytics.

One Resend API call per lead so each recipient gets a unique `resend_message_id`.

Resend tags on send: `workflow_id`, `lead_id` (included in webhook payloads).

## EmailService methods

### `send_email`

Send to a single lead.

- Inputs: `workflow_id`, `lead_id`, `subject`, `html_content`, `plain_text_content`, optional `step_id`
- Calls `ResendProvider.send_email`
- Stores record in MongoDB `email_messages`
- Increments workflow analytics `sent`
- Returns `SendEmailResult` (`resendMessageId`, `workflowId`, `leadId`)

### `send_bulk_email`

Send the same content to many leads (loops `send_email`).

- Returns `BulkSendEmailResult` with `messageIds`, `sentCount`, `failedCount`

### `send_workflow_email`

`POST /api/v1/email/send` helper — first `send_email` step + all workflow recipients via `send_bulk_email`.

### `record_delivery_event`

Updates `email_messages` tracking flags from webhooks by `resend_message_id`.

## Storage (`email_messages` collection)

| Field | Description |
|-------|-------------|
| `resend_message_id` | Resend email id (unique) |
| `workflow_id` | Campaign workflow |
| `lead_id` | Recipient email |
| `step_id` | Optional workflow step |
| `sent` | Set true on successful send |
| `delivered` | Webhook `email.delivered` |
| `opened` | Webhook `email.opened` |
| `clicked` | Webhook `email.clicked` |
| `replied` | Webhook `email.received` |
| `failed` | Send failure or `email.bounced` |

## Tracking

Per-message flags in `email_messages` (updated via webhooks).

Workflow-level counters in `analytics` collection: `sent`, `delivered`, `opened`, `clicked`, `replied`, `failed`, `bounced`.

## Implementation

**Provider**

- `backend/app/providers/email/base.py` — `EmailProvider.send_email`
- `backend/app/providers/email/resend_provider.py` — Resend SDK, tags, async send

**Service**

- `backend/app/services/email_service.py`
- `backend/app/repositories/email_message_repository.py`
- `backend/app/schemas/email_message.py`

**API**

- `POST /api/v1/email/send` — body `{ workflowId }`

**Execution**

- `workflow_execution_service` uses `EmailService.send_email` for `send_email` steps

**Webhooks**

- `webhook_processing_service` calls `record_delivery_event` when `email_id` present

**Config**

- `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `RESEND_WEBHOOK_SECRET`

**Tests**

- `backend/tests/test_resend_email_service.py`

## Check When Done

- Resend connection works
- Email sent successfully
- `resend_message_id` stored with `workflow_id` and `lead_id`
- `send_bulk_email` returns one message id per lead
- Webhooks update delivered / opened / clicked / replied / failed
- Provider abstraction exists
- Errors handled gracefully (failed row + analytics)
- No type errors
