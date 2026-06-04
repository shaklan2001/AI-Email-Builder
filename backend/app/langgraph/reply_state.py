from typing import TypedDict


class ReplyHandlingState(TypedDict, total=False):
    workflow_id: str
    lead_email: str
    reply_body: str
    reply_subject: str | None
    webhook_event_id: str | None
    product_context: str | None
    reply_intent: str
    lead_status: str
