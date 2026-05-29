# 17-human-review-loop.md

Allow users to review and edit generated email content before workflow activation.

## Design

Users should be able to:

- View generated emails
- Edit subject
- Edit HTML
- Edit plain text

Changes should override AI-generated content.

User edits become the final source of truth.

## Implementation

Add:

Email Review Panel

Support:

- Subject editing
- HTML editing
- Plain text editing

Track:

ai_generated_version

final_user_version

Do not regenerate automatically after edits.

Persist edited content in workflow state.

## Check When Done

- User can edit emails
- Changes persist
- Workflow uses edited content
- No data loss