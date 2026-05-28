Reply intent classification for inbound emails.

## Backend intent types (`ReplyIntent`)

- `interested`
- `not_interested`
- `need_more_info`
- `book_demo`

Implemented in `app/schemas/reply_intent.py`, `reply_intent_agent.py`, and `37-reply-handling.md`.

## Frontend (optional)

Display intent label on lead/thread UI when `reply_intent` is present on lead records. Legacy mock labels (COMPANY_INFO, DEMO_REQUEST, etc.) may be mapped in UI only.

## Check When Done

- Intent enum exists (backend)
- Reply classified on webhook `replied`
- UI supports displaying intent (when wired to API)