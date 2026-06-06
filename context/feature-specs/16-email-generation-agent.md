# 16-email-generation-agent.md

Generate email content for workflow steps.

## Design

Each email step should generate:

- Subject
- HTML Email
- Plain Text Email

The AI should use campaign information collected during the conversation.

Generated content should be sales-focused and professional.

## Implementation

Create:

agents/

email_generation_agent.py

copywriter_agent.py  (alias / re-export of email generation agent)

Responsibilities:

- Subject generation
- HTML generation
- Plain text generation

Output Example:

{
  "subject": "...",
  "html_content": "...",
  "plain_text_content": "..."
}

Generate email content for all email steps in the workflow.

Store generated content in:

- Workflow steps (`email` on each `send_email` step — `GeneratedEmailContent` with AI + final versions)
- MongoDB `email_templates` via `email_template_repository`
- Conversation state / `persistence.py`

Email types: promotional (initial), follow-up, reply (inferred via `email_type.py`).

After generation, set `review_status: pending` for review stage (`35-workflow-review-stage.md`).

Expose generated emails through chat API workflow preview.

Update frontend preview (`workflow-preview.tsx`, `email-review-panel.tsx`).

**Tests**

- `backend/tests/test_email_generation_agent.py`

## Check When Done

- Email generation works
- Subject, HTML, and plain text generated
- Workflow state and `email_templates` updated in MongoDB
- Frontend preview updated
- Review stage reachable after emails
- No type errors