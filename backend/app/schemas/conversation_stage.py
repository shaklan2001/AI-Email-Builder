from enum import StrEnum


class ConversationStage(StrEnum):
    DISCOVERY = "discovery"
    CAMPAIGN_BRIEF = "campaign_brief"
    WORKFLOW_GENERATION = "workflow_generation"
    EMAIL_GENERATION = "email_generation"
    REVIEW = "review"
    ACTIVATION = "activation"


STAGES_WITH_WORKFLOW_PREVIEW: frozenset[str] = frozenset(
    {
        ConversationStage.WORKFLOW_GENERATION,
        ConversationStage.EMAIL_GENERATION,
        ConversationStage.REVIEW,
        ConversationStage.ACTIVATION,
    }
)

STAGES_WITH_BRIEF_PREVIEW: frozenset[str] = frozenset(
    {
        ConversationStage.CAMPAIGN_BRIEF,
        ConversationStage.WORKFLOW_GENERATION,
        ConversationStage.EMAIL_GENERATION,
        ConversationStage.REVIEW,
        ConversationStage.ACTIVATION,
    }
)
