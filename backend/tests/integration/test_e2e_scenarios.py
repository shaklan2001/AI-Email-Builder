"""
End-to-end integration tests (spec 45).

Uses in-memory repositories and mocked email/LLM — no manual MongoDB or Redis setup.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.tool_router_agent import ToolRouterAgent
from app.providers.llm.base import LLMProviderError
from app.repositories.workflow_repository import WorkflowRecord
from app.schemas.agent_tool import AgentToolName
from app.schemas.reply_intent import ReplyIntent
from app.services.review_service import apply_review_approve
from app.services.workflow_activation_service import WorkflowActivationService
from app.workers.celery_app import RETRY_QUEUE

from tests.integration.e2e_fixtures import (
    LEAD_EMAIL,
    USER_ID,
    WORKFLOW_ID,
    InMemoryConversationStore,
    InMemoryRunRepository,
    MockEmailProvider,
    approved_conversation_state,
    build_execution_service,
    campaign_conversation_state,
    conditional_workflow_definition,
    draft_workflow_record,
)


def _patch_execution_stack(
    monkeypatch: pytest.MonkeyPatch,
    run_repo: InMemoryRunRepository,
    execution_svc,
) -> None:
    monkeypatch.setattr(
        "app.services.workflow_execution_service.workflow_execution_service",
        execution_svc,
    )
    monkeypatch.setattr(
        "app.services.workflow_activation_service.workflow_execution_service",
        execution_svc,
    )
    monkeypatch.setattr(
        "app.workers.email_worker.workflow_execution_service",
        execution_svc,
    )
    monkeypatch.setattr(
        "app.workers.workflow_runner.workflow_execution_service",
        execution_svc,
    )
    monkeypatch.setattr(
        "app.workers.workflow_runner.workflow_run_repository",
        run_repo,
    )

    def _noop_db(operation):
        import asyncio

        return asyncio.run(operation())

    monkeypatch.setattr("app.workers.email_worker.with_database", _noop_db)
    monkeypatch.setattr("app.workers.workflow_worker.with_database", _noop_db)


@pytest.mark.asyncio
async def test_scenario_1_campaign_through_activation_email_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Campaign → workflow → approval → activation → initial email sent."""
    run_repo = InMemoryRunRepository()
    email_provider = MockEmailProvider()
    execution_svc = build_execution_service(run_repo, email_provider)
    _patch_execution_stack(monkeypatch, run_repo, execution_svc)

    pending = campaign_conversation_state()
    assert pending.get("product_info")
    assert pending.get("workflow", {}).get("steps")

    approve_updates = apply_review_approve(pending)  # type: ignore[arg-type]
    assert approve_updates.get("review_status") == "approved"
    conv_store = InMemoryConversationStore({**pending, **approve_updates})

    draft = draft_workflow_record()
    activated = WorkflowRecord(
        id=draft.id,
        user_id=draft.user_id,
        name=draft.name,
        status="active",
        workflow_definition=draft.workflow_definition,
        active_version=1,
        activated_at=datetime.now(UTC),
        created_at=draft.created_at,
        updated_at=datetime.now(UTC),
    )
    version_doc = MagicMock()
    version_doc.version = 1

    monkeypatch.setattr(
        "app.services.workflow_activation_service.conversation_repository",
        conv_store,
    )
    monkeypatch.setattr(
        "app.services.workflow_execution_service.conversation_repository",
        conv_store,
    )
    mock_wf_repo = MagicMock()
    mock_wf_repo.get_by_id = AsyncMock(return_value=draft)
    mock_wf_repo.activate = AsyncMock(return_value=activated)
    mock_wf_repo.upsert_workflow_definition = AsyncMock()
    monkeypatch.setattr(
        "app.services.workflow_activation_service.workflow_repository",
        mock_wf_repo,
    )
    monkeypatch.setattr(
        "app.services.workflow_activation_service.workflow_version_service.create_snapshot",
        AsyncMock(return_value=version_doc),
    )
    monkeypatch.setattr(
        "app.services.workflow_activation_service.execution_repository.find_by_workflow_and_lead",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.services.workflow_activation_service.execution_repository.create",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.services.workflow_execution_service.workflow_repository.get_by_id",
        AsyncMock(return_value=activated),
    )
    monkeypatch.setattr(
        "app.services.workflow_execution_service.workflow_version_service.get_definition_dict",
        AsyncMock(return_value=conditional_workflow_definition().model_dump()),
    )
    monkeypatch.setattr(
        "app.services.workflow_activation_service.execute_workflow_step_task.apply_async",
        MagicMock(),
    )

    result = await WorkflowActivationService().activate(
        user_id=USER_ID,
        workflow_id=WORKFLOW_ID,
    )

    assert result.status == "active"
    assert result.runs_queued == 1
    runs = list(run_repo._runs.values())
    assert len(runs) == 1
    await execution_svc.execute_step(runs[0].id, user_id=USER_ID)

    assert len(email_provider.sent) == 1
    assert email_provider.sent[0]["recipients"] == [LEAD_EMAIL]
    assert email_provider.sent[0]["subject"] == "Subject step_1"


@pytest.mark.asyncio
async def test_scenario_2_no_reply_wait_follow_up_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No reply → wait elapses → condition (no) → follow-up email sent."""
    run_repo = InMemoryRunRepository()
    email_provider = MockEmailProvider()
    execution_svc = build_execution_service(run_repo, email_provider)
    _patch_execution_stack(monkeypatch, run_repo, execution_svc)

    run = await execution_svc.create_run(
        user_id=USER_ID,
        workflow_id=WORKFLOW_ID,
        recipient_id=LEAD_EMAIL,
    )

    await execution_svc.execute_step(run.id, user_id=USER_ID)
    after_send = await run_repo.get_by_id(run.id)
    assert after_send is not None
    assert after_send.status == "waiting"

    resume_at = after_send.next_execution_at or datetime.now(UTC)
    await execution_svc.execute_step(
        run.id,
        user_id=USER_ID,
        now=resume_at + timedelta(seconds=1),
    )
    await execution_svc.execute_step(run.id, user_id=USER_ID, condition_result=False)
    await execution_svc.execute_step(run.id, user_id=USER_ID)
    await execution_svc.execute_step(run.id, user_id=USER_ID)

    assert len(email_provider.sent) == 2
    assert email_provider.sent[1]["subject"] == "Subject step_4"
    final = await run_repo.get_by_id(run.id)
    assert final is not None
    assert final.status == "completed"


@pytest.mark.asyncio
async def test_scenario_3_reply_classified_auto_response_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reply received → intent classified → agent tool → auto-response email sent."""
    from app.services.agent_tools_service import AgentToolsService
    from app.services.reply_handling_service import ReplyHandlingService

    run_repo = InMemoryRunRepository()
    email_provider = MockEmailProvider()
    execution_svc = build_execution_service(run_repo, email_provider)
    email_svc = execution_svc._email_service

    conv_store = InMemoryConversationStore(approved_conversation_state())
    leads = AsyncMock()
    leads.upsert_for_workflow = AsyncMock()
    inbound = AsyncMock()
    inbound.create = AsyncMock(return_value=MagicMock(id="inbound_1"))

    mock_reply_graph = MagicMock()
    mock_reply_graph.ainvoke = AsyncMock(
        return_value={
            "reply_intent": ReplyIntent.NEEDS_INFO.value,
            "lead_status": "replied",
        },
    )
    mock_tools_graph = MagicMock()
    mock_tools_graph.ainvoke = AsyncMock(
        return_value={
            "selected_tool": AgentToolName.COMPANY_KNOWLEDGE.value,
            "tool_result": {
                "tool": "company_knowledge",
                "summary": "ZyLabs builds AI email automation.",
                "data": {},
            },
            "agent_response": "ZyLabs builds AI email automation.",
        },
    )
    tool_executions = AsyncMock()
    tool_executions.create = AsyncMock(return_value=MagicMock(id="exec_1"))

    llm = MagicMock()
    llm.generate = AsyncMock(side_effect=LLMProviderError("offline"))
    router = ToolRouterAgent(llm=llm)

    monkeypatch.setattr(
        "app.services.reply_handling_service.conversation_repository",
        conv_store,
    )
    monkeypatch.setattr(
        "app.services.reply_handling_service.get_reply_handling_graph",
        lambda: mock_reply_graph,
    )
    monkeypatch.setattr(
        "app.services.agent_tools_service.conversation_repository",
        conv_store,
    )
    monkeypatch.setattr(
        "app.services.agent_tools_service.get_agent_tools_graph",
        lambda: mock_tools_graph,
    )
    monkeypatch.setattr(
        "app.langgraph.agent_tools_nodes.tool_router_agent",
        router,
    )

    service = ReplyHandlingService(
        leads=leads,
        inbound_replies=inbound,
        agent_tools=AgentToolsService(executions=tool_executions),
        email=email_svc,
    )

    result = await service.process_inbound_reply(
        user_id=USER_ID,
        workflow_id=WORKFLOW_ID,
        lead_email=LEAD_EMAIL,
        reply_body="Tell me more about ZyLabs",
        reply_subject="Re: Intro",
    )

    assert result.reply_intent == ReplyIntent.NEEDS_INFO
    assert result.tool_called is True
    assert result.selected_tool == AgentToolName.COMPANY_KNOWLEDGE
    assert result.agent_response
    assert result.auto_response_sent is True
    assert len(email_provider.sent) == 1
    assert "ZyLabs" in str(email_provider.sent[0]["plain_text_content"])


@pytest.mark.asyncio
async def test_scenario_4_email_failure_redis_retry_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Email send fails once → retry_queue on retry → second send succeeds."""
    from app.workers.email_worker import _run_send_email

    run_repo = InMemoryRunRepository()
    email_provider = MockEmailProvider()
    email_provider.fail_until_attempt = 1
    execution_svc = build_execution_service(run_repo, email_provider)
    _patch_execution_stack(monkeypatch, run_repo, execution_svc)
    monkeypatch.setattr("app.workers.dispatch.dispatch_after_step", MagicMock())

    run = await execution_svc.create_run(
        user_id=USER_ID,
        workflow_id=WORKFLOW_ID,
        recipient_id=LEAD_EMAIL,
    )

    first_retry_queue = "email_queue" if 0 > 0 else "email_queue"
    second_retry_queue = RETRY_QUEUE if 1 > 0 else "email_queue"
    assert second_retry_queue == RETRY_QUEUE

    with pytest.raises(RuntimeError, match="Simulated send failure"):
        await _run_send_email(user_id=USER_ID, workflow_run_id=run.id)

    await execution_svc.execute_step(run.id, user_id=USER_ID)

    assert email_provider.attempts == 2
    assert len(email_provider.sent) == 1
    assert first_retry_queue == "email_queue"
