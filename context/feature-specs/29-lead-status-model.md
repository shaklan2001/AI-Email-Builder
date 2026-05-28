Prepare lead lifecycle tracking.

## Lead Status

NEW

EMAIL_SENT

OPENED

CLICKED

REPLIED

INTERESTED

DEMO_BOOKED

NOT_INTERESTED

UNSUBSCRIBED

CLOSED

## Workflow Review

Add Lead Status section.

Mock data is acceptable.

Backend: `LeadStatus` in `app/schemas/enums.py`; `leads` collection updated by reply handling (`37-reply-handling.md`) and execution send paths.

| Reply intent | `LeadStatus` |
|--------------|--------------|
| interested | `interested` |
| not_interested | `not_interested` |
| need_more_info | `replied` |
| book_demo | `booked_demo` |

## Check When Done

- Status enum exists
- Review panel displays statuses
- Reply handling updates lead status automatically