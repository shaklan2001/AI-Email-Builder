# AI-Driven Email Workflow Builder

## Overview

AI-Driven Email Workflow Builder is a conversational AI platform that enables sales and
marketing teams to create and execute email campaigns through natural language conversation.
Instead of manually configuring workflow builders, users describe their campaign goals to an
AI assistant that collects requirements, designs workflow logic, generates email content,
validates recipients, and activates automated execution — all within a single chat interface.

## Goals

1. A user can describe a campaign in plain English and receive a fully generated workflow
   with email content ready to activate — without touching a drag-and-drop builder.
2. Workflows execute automatically after approval: emails send, wait steps pause, and
   reply/no-reply branches route without manual intervention.
3. Users can track campaign engagement (sent, delivered, opened, clicked, replied, failed)
   per workflow from a live analytics view.

## Core User Flow

1. User signs in via Clerk authentication.
2. User opens a new campaign and types a goal (e.g. "I want to run a cold outreach campaign for my air purifier").
3. AI collects requirements through conversation: audience, tone, CTA, follow-up logic, wait periods.
4. AI generates workflow definition (send → wait → condition → follow-up) and previews it live in the right panel.
5. AI generates email content: subject, HTML, plain text. Preview updates in real time.
6. User uploads a CSV or enters recipients manually. System validates and reports invalid rows.
7. User reviews the workflow and email preview, edits or regenerates if needed.
8. User approves and activates the workflow.
9. System queues execution. Celery workers send emails via Resend.
10. Reply webhooks evaluate conditions and route to YES/NO branches automatically.
11. User monitors engagement on the analytics page.

## Features

### AI Campaign Builder

- Conversational requirement gathering (business goal, audience, tone, CTA, follow-up logic)
- Live workflow preview that updates as AI collects information
- Live email preview (subject, HTML, plain text) updating in real time
- Email regeneration on user instruction (e.g. "make it more professional")

### Recipient Management

- CSV upload with validation (invalid format, duplicates, missing values)
- Manual recipient entry
- Validation report with row-level error details
- User choice: continue with valid, fix, or cancel

### Workflow Engine

- Supported steps: Send Email, Wait (N days), Condition (reply received?), End
- Conditional branching: YES path and NO path per condition step
- Celery-based async execution — no thread sleeps
- Delayed execution via Redis eta (wait steps)

### Email Delivery

- Resend as email provider
- Personalization variable injection: `{{first_name}}`, `{{company_name}}`, `{{email}}`
- Delivery, open, click, reply, and bounce tracking via Resend webhooks

### Analytics

- Per-workflow metrics: sent, delivered, opened, clicked, replied, failed, bounced
- Metrics updated in real time via incoming webhook events

## Scope

### In Scope (MVP)

- Conversational AI campaign builder
- CSV and manual recipient upload with validation
- AI-generated workflow logic (no manual node builder)
- AI-generated email content with regeneration support
- Workflow activation and async execution
- Wait step scheduling via Celery eta
- Reply detection via Resend webhooks
- Conditional branch routing (reply / no-reply)
- Per-workflow analytics dashboard
- Clerk authentication

### Out of Scope (Not MVP)

- Custom sending domains
- A/B testing
- Multi-tenant / organization support
- CRM integrations
- SMS or WhatsApp campaigns
- Slack notifications
- Workflow versioning
- Per-recipient AI personalization
- Manual drag-and-drop workflow builder

## Success Criteria

1. A signed-in user can describe a campaign, receive a generated workflow and email, upload recipients, and activate — end to end — without any manual workflow configuration.
2. After activation, emails are sent automatically to all valid recipients with correct personalization variables injected.
3. A reply from a recipient triggers the YES branch of a condition step within 60 seconds of the Resend webhook being received.
4. The analytics page reflects accurate sent/delivered/opened/replied counts updated per webhook event.
5. Uploading a CSV with invalid rows returns a row-level validation report and does not save invalid recipients.
