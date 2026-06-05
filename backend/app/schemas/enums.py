from enum import StrEnum


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class LeadStatus(StrEnum):
    PENDING = "pending"
    EMAILED = "emailed"
    REPLIED = "replied"
    INTERESTED = "interested"
    BOOKED_DEMO = "booked_demo"
    NOT_INTERESTED = "not_interested"


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
