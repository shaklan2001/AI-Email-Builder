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

copywriter_agent.py

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

Store generated content in workflow state.

Expose generated emails through API.

Update frontend preview.

## Check When Done

- Email generation works
- Subject generated
- HTML generated
- Plain text generated
- Workflow state updated
- Frontend preview updated