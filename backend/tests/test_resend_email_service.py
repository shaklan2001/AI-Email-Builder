"""Resend EmailService — send, bulk send, message id storage, tracking."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.repositories.email_message_repository import EmailMessageRecord
from app.services.email_service import EmailService


class FakeEmailProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self._counter = 0

    async def send_email(
        self,
        *,
        subject: str,
        html_content: str,
        plain_text_content: str,
        recipients: list[str],
        workflow_id: str | None = None,
        lead_id: str | None = None,
    ) -> str:
        self._counter += 1
        self.calls.append(
            {
                "subject": subject,
                "recipients": recipients,
                "workflow_id": workflow_id,
                "lead_id": lead_id,
            },
        )
        return f"msg_{self._counter}"


@pytest.mark.asyncio
async def test_send_email_stores_message_id_and_marks_sent() -> None:
    provider = FakeEmailProvider()
    repo = MagicMock()
    repo.create_sent = AsyncMock(
        return_value=EmailMessageRecord(
            id="rec_1",
            resend_message_id="msg_1",
            workflow_id="wf_test",
            lead_id="a@example.com",
            step_id="s1",
            sent=True,
            delivered=False,
            opened=False,
            clicked=False,
            replied=False,
            failed=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    )
    analytics = MagicMock()
    analytics.record_sent = AsyncMock()

    service = EmailService(
        email_provider=provider,
        message_repository=repo,
        analytics=analytics,
    )

    result = await service.send_email(
        workflow_id="wf_test",
        lead_id="a@example.com",
        subject="Hello",
        html_content="<p>Hi</p>",
        plain_text_content="Hi",
        step_id="s1",
    )

    assert result.resend_message_id == "msg_1"
    assert result.workflow_id == "wf_test"
    assert result.lead_id == "a@example.com"
    repo.create_sent.assert_awaited_once_with(
        resend_message_id="msg_1",
        workflow_id="wf_test",
        lead_id="a@example.com",
        step_id="s1",
    )
    analytics.record_sent.assert_awaited_once_with("wf_test")
    assert provider.calls[0]["workflow_id"] == "wf_test"
    assert provider.calls[0]["lead_id"] == "a@example.com"


@pytest.mark.asyncio
async def test_send_bulk_email_one_message_id_per_lead() -> None:
    provider = FakeEmailProvider()
    repo = MagicMock()
    repo.create_sent = AsyncMock(
        side_effect=lambda **kwargs: EmailMessageRecord(
            id="x",
            resend_message_id=kwargs["resend_message_id"],
            workflow_id=kwargs["workflow_id"],
            lead_id=kwargs["lead_id"],
            step_id=kwargs.get("step_id"),
            sent=True,
            delivered=False,
            opened=False,
            clicked=False,
            replied=False,
            failed=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    )
    analytics = MagicMock()
    analytics.record_sent = AsyncMock()

    service = EmailService(
        email_provider=provider,
        message_repository=repo,
        analytics=analytics,
    )

    bulk = await service.send_bulk_email(
        workflow_id="wf_bulk",
        lead_ids=["a@example.com", "b@example.com"],
        subject="Hi",
        html_content="<p>x</p>",
        plain_text_content="x",
        step_id="s1",
    )

    assert bulk.sent_count == 2
    assert bulk.message_ids == ["msg_1", "msg_2"]
    assert len(bulk.results) == 2
    assert repo.create_sent.await_count == 2


@pytest.mark.asyncio
async def test_record_delivery_event_updates_tracking() -> None:
    repo = MagicMock()
    repo.apply_tracking_event = AsyncMock(return_value=MagicMock())

    service = EmailService(message_repository=repo)
    await service.record_delivery_event(
        resend_message_id="msg_abc",
        event_type="delivered",
    )

    repo.apply_tracking_event.assert_awaited_once_with(
        "msg_abc",
        event="delivered",
    )


@pytest.mark.asyncio
async def test_send_email_invalid_lead_raises() -> None:
    service = EmailService(email_provider=FakeEmailProvider())
    with pytest.raises(HTTPException) as exc:
        await service.send_email(
            workflow_id="wf_x",
            lead_id="not-an-email",
            subject="S",
            html_content="<p>x</p>",
            plain_text_content="x",
        )
    assert exc.value.status_code == 400
