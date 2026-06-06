"""Tests for workflow analytics (spec 23)."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from svix.webhooks import Webhook

from app.models.analytics import WorkflowAnalytics
from app.models.webhook_event import WebhookEvent
from app.models.workflow_run import WorkflowRun
from app.repositories.workflow_repository import WorkflowRecord
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.analytics_service import AnalyticsService, WEBHOOK_METRIC_MAP
from app.services.webhook_processing_service import WebhookProcessingService

WEBHOOK_SECRET = "whsec_test_secret_for_webhook_verification_only"


@pytest.mark.asyncio
async def test_record_webhook_event_increments_mapped_metrics() -> None:
    repo = AsyncMock()
    repo.increment = AsyncMock(
        return_value=WorkflowAnalytics(
            workflow_id="wf_1",
            delivered=1,
            updated_at=datetime.now(UTC),
        ),
    )
    service = AnalyticsService(repository=repo)

    result = await service.record_webhook_event("wf_1", "delivered")
    assert result is not None
    repo.increment.assert_called_once_with("wf_1", metric="delivered", amount=1)

    repo.increment.reset_mock()
    assert await service.record_webhook_event("wf_1", "unknown") is None  # type: ignore[arg-type]
    repo.increment.assert_not_called()


def test_webhook_metric_map_covers_supported_events() -> None:
    assert set(WEBHOOK_METRIC_MAP) == {"delivered", "opened", "clicked", "replied", "bounced"}


@pytest.mark.asyncio
async def test_get_for_user_returns_zeros_when_no_metrics_doc() -> None:
    workflow_repo = AsyncMock()
    workflow_repo.get_by_id = AsyncMock(
        return_value=WorkflowRecord(
            id="wf_1",
            user_id="user_1",
            name="Test",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    )
    analytics_repo = AsyncMock()
    analytics_repo.get_by_workflow_id = AsyncMock(return_value=None)
    service = AnalyticsService(repository=analytics_repo, workflow_repo=workflow_repo)

    metrics = await service.get_for_user(user_id="user_1", workflow_id="wf_1")
    assert metrics.sent == 0
    assert metrics.delivered == 0
    assert metrics.workflow_id == "wf_1"


@pytest.mark.asyncio
async def test_get_for_user_raises_when_workflow_missing() -> None:
    workflow_repo = AsyncMock()
    workflow_repo.get_by_id = AsyncMock(return_value=None)
    service = AnalyticsService(repository=AsyncMock(), workflow_repo=workflow_repo)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_for_user(user_id="user_1", workflow_id="wf_missing")
    assert exc_info.value.status_code == 404


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


@pytest.fixture(autouse=True)
def webhook_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.webhook_processing_service.settings.resend_webhook_secret",
        WEBHOOK_SECRET,
    )


@pytest.mark.asyncio
async def test_delivered_webhook_updates_analytics() -> None:
    now = datetime.now(UTC)
    run = WorkflowRun(
        id="run_1",
        workflow_id="wf_1",
        recipient_id="lead@example.com",
        current_step="step_1",
        status="queued",
        next_execution_at=now,
        created_at=now,
        updated_at=now,
    )
    event_repo = AsyncMock()
    event_repo.get_by_event_id = AsyncMock(return_value=None)
    event_repo.create = AsyncMock(
        return_value=WebhookEvent(
            id="wh_2",
            event_id="msg_test_event_1",
            event_type="delivered",
            timestamp=now,
            recipient="lead@example.com",
            workflow_id="wf_1",
            processed=False,
            created_at=now,
        ),
    )
    run_repo = AsyncMock()
    run_repo.find_active_by_recipient = AsyncMock(return_value=[run])
    workflow_repo = AsyncMock()
    workflow_repo.get_by_id_only = AsyncMock(
        return_value=WorkflowRecord(
            id="wf_1",
            user_id="user_1",
            name="Test",
            status="active",
            workflow_definition=WorkflowDefinition(
                workflow_type="linear",
                steps=[WorkflowStep(id="step_1", type="send_email", name="Initial")],
            ).model_dump(),
            created_at=now,
            updated_at=now,
        ),
    )
    execution_service = AsyncMock()
    analytics = AsyncMock()
    analytics.record_webhook_event = AsyncMock()
    email_svc = AsyncMock()
    email_svc.record_delivery_event = AsyncMock()
    service = WebhookProcessingService(
        event_repository=event_repo,
        run_repository=run_repo,
        workflow_repo=workflow_repo,
        execution_service=execution_service,
        analytics=analytics,
        email=email_svc,
    )
    body, headers = _sign_payload(_delivered_payload())
    with patch("app.services.webhook_processing_service.dispatch_after_step"):
        await service.process(payload=body, headers=headers)
    analytics.record_webhook_event.assert_called_once_with("wf_1", "delivered")
