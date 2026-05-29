# 19-resend-email.md

Integrate Resend as the email delivery provider.

The goal is to send generated emails through Resend.

Do not implement workflow scheduling yet.

Only support immediate email sending.

## Design

Email sending should be abstracted behind a provider layer.

Future providers should be swappable.

Use the existing provider pattern.

## Implementation

Create:

providers/email/

- base.py
- resend_provider.py

Create EmailProvider interface.

Methods:

- send_email()

Implement:

ResendProvider

Configuration:

RESEND_API_KEY

Support:

- subject
- html content
- plain text content
- recipient list

Create:

EmailService

Responsibilities:

- provider selection
- email validation
- send orchestration

Add endpoint:

POST /api/v1/email/send

Request:

{
  workflow_id
}

Use workflow data from MongoDB.

Return send status.

## Check When Done

- Resend connection works
- Emails send successfully
- Provider abstraction exists
- Errors handled gracefully
- No type errors