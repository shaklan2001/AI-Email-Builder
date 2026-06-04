"""Tests for Resend webhook processing (spec 22)."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from svix.webhooks import Webhook

from app.models.webhook_event import WebhookEvent
from app.models.workflow_run import WorkflowRun
from app.repositories.workflow_repository import WorkflowRecord
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.schemas.agent_tool import AgentToolName
from app.schemas.reply_intent import ReplyIntent
from app.schemas.enums import LeadStatus
from app.services.reply_handling_service import ReplyHandlingResult
from app.services.webhook_processing_service import WebhookProcessingService
from app.services.workflow_execution_service import StepExecutionResult


WEBHOOK_SECRET = "whsec_test_secret_for_webhook_verification_only"


def _sign_payload(payload: dict[str, object], *, event_id: str = "msg_test_event_1") -> tuple[bytes, dict[str, str]]:
    body_str = json.dumps(payload)
    body = body_str.encode()
    wh = Webhook(WEBHOOK_SECRET)
    timestamp = datetime.now(UTC)
    signature = wh.sign(event_id, timestamp, body_str)
    headers = {
        "svix-id": event_id,
        "svix-timestamp": str(int(timestamp.timestamp())),
        "svix-signature": signature,
    }
    return body, headers


def _reply_payload(*, from_email: str = "lead@example.com") -> dict[str, object]:
    return {
        "type": "email.received",
        "created_at": "2026-06-04T12:00:00.000Z",
        "data": {
            "email_id": "email_123",
            "from": from_email,
            "to": ["onboarding@resend.dev"],
            "subject": "Re: Hello",
        },
    }


def _delivered_payload(*, to_email: str = "lead@example.com") -> dict[str, object]:
    return {
        "type": "email.delivered",
        "created_at": "2026-06-04T12:00:00.000Z",
        "data": {
            "email_id": "email_456",
            "to": [to_email],
            "from": "Acme <onboarding@resend.dev>",
            "subject": "Hello",
        },
    }


@pytest.fixture
def event_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_event_id = AsyncMock(return_value=None)
    repo.create = AsyncMock(
        return_value=WebhookEvent(
            id="wh_1",
            event_id="msg_test_event_1",
            event_type="replied",
            timestamp=datetime.now(UTC),
            recipient="lead@example.com",
            workflow_id="wf_1",
            processed=False,
            created_at=datetime.now(UTC),
        ),
    )
    repo.mark_processed = AsyncMock()
    return repo


@pytest.fixture
def run_repo() -> AsyncMock:
    now = datetime.now(UTC)
    run = WorkflowRun(
        id="run_1",
        workflow_id="wf_1",
        recipient_id="lead@example.com",
        current_step="step_3",
        status="queued",
        next_execution_at=now,
        created_at=now,
        updated_at=now,
    )
    repo = AsyncMock()
    repo.find_active_by_recipient = AsyncMock(return_value=[run])
    repo.get_by_id = AsyncMock(return_value=run)
    repo.update = AsyncMock(return_value=run)
    return repo


@pytest.fixture
def workflow_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id_only = AsyncMock(
        return_value=WorkflowRecord(
            id="wf_1",
            user_id="user_1",
            name="Test",
            status="active",
            workflow_definition=_sample_definition().model_dump(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    )
    repo.get_by_id = AsyncMock(
        return_value=WorkflowRecord(
            id="wf_1",
            user_id="user_1",
            name="Test",
            status="active",
            workflow_definition=_sample_definition().model_dump(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    )
    return repo


@pytest.fixture
def execution_service() -> AsyncMock:
    svc = AsyncMock()
    svc._next_linear_step_id = MagicMock(return_value=None)
    svc.execute_step = AsyncMock(
        return_value=StepExecutionResult(
            workflow_run_id="run_1",
            step_id="step_3",
            step_type="condition",
            action="evaluated_condition",
            status="queued",
            next_step_id="step_5",
        ),
    )
    return svc


@pytest.fixture
def analytics_service() -> AsyncMock:
    svc = AsyncMock()
    svc.record_webhook_event = AsyncMock()
    return svc


@pytest.fixture
def email_service() -> AsyncMock:
    mock = AsyncMock()
    mock.record_delivery_event = AsyncMock()
    return mock


@pytest.fixture
def reply_handler() -> AsyncMock:
    mock = AsyncMock()
    mock.process_inbound_reply = AsyncMock(
        return_value=ReplyHandlingResult(
            workflow_id="wf_1",
            lead_email="lead@example.com",
            reply_intent=ReplyIntent.NEED_MORE_INFO,
            lead_status=LeadStatus.REPLIED,
            lead_updated=True,
            reply_stored=True,
            tool_called=True,
            selected_tool=AgentToolName.COMPANY_KNOWLEDGE,
            tool_result={"tool": "company_knowledge", "summary": "Info about ZyLabs"},
            agent_response="Info about ZyLabs",
            auto_response_sent=True,
        ),
    )
    return mock


@pytest.fixture
def service(
    event_repo: AsyncMock,
    run_repo: AsyncMock,
    workflow_repo: AsyncMock,
    execution_service: AsyncMock,
    analytics_service: AsyncMock,
    email_service: AsyncMock,
    reply_handler: AsyncMock,
) -> WebhookProcessingService:
    return WebhookProcessingService(
        event_repository=event_repo,
        run_repository=run_repo,
        workflow_repo=workflow_repo,
        execution_service=execution_service,
        analytics=analytics_service,
        email=email_service,
        reply_handler=reply_handler,
    )


def _sample_definition() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_type="conditional",
        steps=[
            WorkflowStep(id="step_1", type="send_email", name="Initial"),
            WorkflowStep(id="step_2", type="wait", days=3),
            WorkflowStep(id="step_3", type="condition", condition="reply_received"),
            WorkflowStep(id="step_4", type="send_email", name="Follow Up", branch="no"),
            WorkflowStep(id="step_5", type="send_email", name="Demo Call", branch="yes"),
            WorkflowStep(id="step_6", type="end"),
        ],
    )


@pytest.fixture(autouse=True)
def webhook_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.webhook_processing_service.settings.resend_webhook_secret",
        WEBHOOK_SECRET,
    )


@pytest.mark.asyncio
async def test_invalid_signature_rejected(service: WebhookProcessingService) -> None:
    payload = json.dumps(_reply_payload()).encode()
    headers = {
        "svix-id": "msg_bad",
        "svix-timestamp": "123",
        "svix-signature": "v1,invalid",
    }
    with pytest.raises(HTTPException) as exc_info:
        await service.process(payload=payload, headers=headers)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_event_not_reprocessed(
    service: WebhookProcessingService,
    event_repo: AsyncMock,
) -> None:
    event_repo.get_by_event_id = AsyncMock(
        return_value=WebhookEvent(
            id="wh_existing",
            event_id="msg_test_event_1",
            event_type="replied",
            timestamp=datetime.now(UTC),
            recipient="lead@example.com",
            workflow_id="wf_1",
            processed=True,
            created_at=datetime.now(UTC),
        ),
    )
    body, headers = _sign_payload(_reply_payload())
    result = await service.process(payload=body, headers=headers)
    assert result.duplicate is True
    event_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_reply_event_stored_and_updates_workflow(
    service: WebhookProcessingService,
    event_repo: AsyncMock,
    execution_service: AsyncMock,
    analytics_service: AsyncMock,
    reply_handler: AsyncMock,
) -> None:
    body, headers = _sign_payload(_reply_payload())
    with patch("app.services.webhook_processing_service.dispatch_after_step") as mock_dispatch:
        result = await service.process(payload=body, headers=headers)

    assert result.event_type == "replied"
    assert result.workflow_updated is True
    assert result.reply_classified is True
    assert result.reply_intent == ReplyIntent.NEED_MORE_INFO.value
    assert result.lead_updated is True
    assert result.tool_called is True
    assert result.selected_tool == AgentToolName.COMPANY_KNOWLEDGE.value
    reply_handler.process_inbound_reply.assert_called_once()
    event_repo.create.assert_called_once()
    create_kwargs = event_repo.create.call_args.kwargs
    assert create_kwargs["event_type"] == "replied"
    assert create_kwargs["recipient"] == "lead@example.com"
    assert create_kwargs["workflow_id"] == "wf_1"
    execution_service.execute_step.assert_called_once_with(
        "run_1",
        user_id="user_1",
        condition_result=True,
    )
    mock_dispatch.assert_called_once()
    event_repo.mark_processed.assert_called_once()
    analytics_service.record_webhook_event.assert_called_once_with("wf_1", "replied")


@pytest.mark.asyncio
async def test_delivered_event_stored_without_workflow_update(
    service: WebhookProcessingService,
    event_repo: AsyncMock,
    execution_service: AsyncMock,
    analytics_service: AsyncMock,
) -> None:
    event_repo.create = AsyncMock(
        return_value=WebhookEvent(
            id="wh_2",
            event_id="msg_test_event_1",
            event_type="delivered",
            timestamp=datetime.now(UTC),
            recipient="lead@example.com",
            workflow_id="wf_1",
            processed=False,
            created_at=datetime.now(UTC),
        ),
    )
    body, headers = _sign_payload(_delivered_payload())
    result = await service.process(payload=body, headers=headers)

    assert result.event_type == "delivered"
    assert result.workflow_updated is False
    event_repo.create.assert_called_once()
    execution_service.execute_step.assert_not_called()
    analytics_service.record_webhook_event.assert_called_once_with("wf_1", "delivered")


@pytest.mark.asyncio
async def test_supported_event_types_mapped() -> None:
    assert WebhookProcessingService._normalize_event_type("email.opened") == "opened"
    assert WebhookProcessingService._normalize_event_type("email.clicked") == "clicked"
    assert WebhookProcessingService._normalize_event_type("email.bounced") == "bounced"
    assert WebhookProcessingService._normalize_event_type("email.unknown") is None
