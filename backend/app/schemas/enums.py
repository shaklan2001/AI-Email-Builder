from enum import StrEnum


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class ApprovalStatus(StrEnum):
    COLLECTING = "collecting"
    BRIEF_PENDING = "brief_pending"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    ACTIVE = "active"


class LeadStatus(StrEnum):
    NEW = "new"
    EMAIL_SENT = "email_sent"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    INTERESTED = "interested"
    NEEDS_INFO = "needs_info"
    BOOKED_DEMO = "booked_demo"
    NOT_INTERESTED = "not_interested"
    UNSUBSCRIBED = "unsubscribed"


LEGACY_LEAD_STATUS_MAP: dict[str, LeadStatus] = {
    "pending": LeadStatus.NEW,
    "emailed": LeadStatus.EMAIL_SENT,
    "new": LeadStatus.NEW,
    "email_sent": LeadStatus.EMAIL_SENT,
    "opened": LeadStatus.OPENED,
    "clicked": LeadStatus.CLICKED,
    "replied": LeadStatus.REPLIED,
    "interested": LeadStatus.INTERESTED,
    "needs_info": LeadStatus.NEEDS_INFO,
    "need_more_info": LeadStatus.NEEDS_INFO,
    "booked_demo": LeadStatus.BOOKED_DEMO,
    "book_demo": LeadStatus.BOOKED_DEMO,
    "not_interested": LeadStatus.NOT_INTERESTED,
    "unsubscribed": LeadStatus.UNSUBSCRIBED,
}


def normalize_lead_status(value: str | LeadStatus | None) -> LeadStatus:
    if isinstance(value, LeadStatus):
        return value
    if not value:
        return LeadStatus.NEW
    key = str(value).strip().lower()
    return LEGACY_LEAD_STATUS_MAP.get(key, LeadStatus.NEW)


# Status progression rank — higher rank wins on upsert unless explicit override.
LEAD_STATUS_RANK: dict[LeadStatus, int] = {
    LeadStatus.NEW: 0,
    LeadStatus.EMAIL_SENT: 1,
    LeadStatus.OPENED: 2,
    LeadStatus.CLICKED: 3,
    LeadStatus.REPLIED: 4,
    LeadStatus.NEEDS_INFO: 5,
    LeadStatus.INTERESTED: 6,
    LeadStatus.BOOKED_DEMO: 7,
    LeadStatus.NOT_INTERESTED: 8,
    LeadStatus.UNSUBSCRIBED: 9,
}


class ExecutionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


class EmailEventType(StrEnum):
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"


class ThreadMessageRole(StrEnum):
    AGENT = "agent"
    PROSPECT = "prospect"


class ThreadMessageKind(StrEnum):
    AGENT_MESSAGE = "agent_message"
    PROSPECT_REPLY = "prospect_reply"
    AGENT_RESPONSE = "agent_response"
