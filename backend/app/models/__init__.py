from app.models.campaign import Campaign
from app.models.conversation_thread import ConversationThread
from app.models.email_event import EmailEvent
from app.models.email_template import EmailTemplate
from app.models.execution import Execution
from app.models.lead import Lead
from app.models.user import User
from app.models.workflow import Workflow
from app.models.workflow_run import WorkflowRun, WorkflowRunStatus
from app.models.workflow_version import WorkflowVersion

BEANIE_DOCUMENT_MODELS: list[type] = [
    User,
    Campaign,
    Workflow,
    WorkflowVersion,
    Lead,
    EmailTemplate,
    Execution,
    EmailEvent,
    ConversationThread,
]

__all__ = [
    "BEANIE_DOCUMENT_MODELS",
    "Campaign",
    "ConversationThread",
    "EmailEvent",
    "EmailTemplate",
    "Execution",
    "Lead",
    "User",
    "Workflow",
    "WorkflowRun",
    "WorkflowRunStatus",
    "WorkflowVersion",
]
