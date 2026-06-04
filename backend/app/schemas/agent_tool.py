from enum import StrEnum


class AgentToolName(StrEnum):
    COMPANY_KNOWLEDGE = "company_knowledge"
    CALENDAR_BOOKING = "calendar_booking"
    NONE = "none"


AGENT_TOOL_VALUES: frozenset[str] = frozenset(m.value for m in AgentToolName)
