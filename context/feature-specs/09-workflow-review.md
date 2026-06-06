# 09-workflow-review.md

Workflow review UI — summary sections before approval.

**Backend approval, API, and activation gate:** see `35-workflow-review-stage.md`.

## Purpose

Present a read-only summary so the user can approve the campaign before activation.

## Show

- Workflow Summary (name, description, steps)
- Email Summary (subject, body preview)
- Recipient Count
- Schedule Summary
- Lead Status (chips per lifecycle status — mock counts until analytics wired)
- Lead Details (mock list with reply intent when available — see `31-reply-intent-model.md`)

## Actions (UI)

- **Looks Good** — approve via chat or `POST /api/v1/review/{id}/approve`
- **Edit Campaign** — chat action to reopen brief
- **Regenerate Workflow** — chat action to rebuild workflow from brief
- **Activate Workflow** — after approval; see `36-workflow-activation.md`

## Implementation

**Frontend**

- `/workflows/:workflowId/review` — `WorkflowReviewPage`
- `components/review/workflow-review.tsx`
- `components/builder/workflow-review-panel.tsx` — builder preview footer
- `types/workflow-review.ts`, `services/review.service.ts`
- `mocks/workflow-review.ts` — lead status/details extras when API omits them

**Backend**

- Implemented in `35-workflow-review-stage.md` (not mock-only)

## Check When Done

- All summary sections render
- Review actions call API or chat
- Activation button visible only when `activationAllowed`
- No type errors
