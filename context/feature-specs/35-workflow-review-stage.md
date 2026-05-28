# 35-workflow-review-stage.md

Workflow review and user approval before activation.

Replaces mock-only scope in `09-workflow-review.md` (UI sections remain valid; backend is defined here).

## Purpose

Allow user approval of the generated workflow and emails. Block activation until approved.

## Flow position

```
… → Email generation (16) → Review (this spec) → Activation (36)
```

## Actions

| User action | Effect |
|-------------|--------|
| **Looks Good** | `review_status` → `approved`; activation unlocked |
| **Edit Campaign** | `review_status` → `editing`; brief reopened for changes |
| **Regenerate Workflow** | Clears workflow/emails; sets `regenerate_workflow`; graph regenerates from approved brief |

Activation is **not** allowed while `review_status != "approved"`.

## Design

- Stage `review` until approved; then `activation` (`app/services/conversation_stage.py`).
- Chat messages matching review phrases are handled before LangGraph (`review_actions.py`).
- Dedicated review page loads real summary data from API; lead status/details may use mocks where not yet persisted.

## Implementation

**Backend**

- `backend/app/services/review_actions.py` — parse approve / edit / regenerate
- `backend/app/services/review_service.py` — `build_review_data()`, approve handler
- `backend/app/api/review.py` — `GET /api/v1/review/{workflowId}`, `POST …/approve`
- `backend/app/services/chat_service.py` — review actions short-circuit graph when workflow exists
- State: `review_status` (`pending` | `approved` | `editing`) on conversation + MongoDB
- `workflow_activation_service` — 403 if not approved

**Frontend**

- `frontend/src/components/builder/workflow-review-panel.tsx` — Looks Good / Edit Campaign / Regenerate Workflow
- `frontend/src/pages/WorkflowReviewPage.tsx` — API-backed review + approve
- `frontend/src/services/review.service.ts`
- Chat thread exposes `reviewStatus`, `activationAllowed` (`chat_thread_service.py`)

**Tests**

- `backend/tests/test_review_stage.py`

## Check When Done

- Review screen works (builder panel + `/workflows/:id/review`)
- Approval stored (`review_status: approved` in MongoDB)
- Activation API returns 403 before approval
- Edit and regenerate routes behave as specified
- Frontend shows locked/unlocked activation messaging
- No type errors
