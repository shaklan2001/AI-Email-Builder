"""Workflow generation agent (generation node types + follow-up delay)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.workflow_agent import WorkflowAgent, _validate_workflow_payload
from app.schemas.follow_up_delay import FollowUpDelay
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.persistence import save_conversation_state
from app.services.workflow_structure import (
    build_canonical_workflow,
    build_no_follow_up_workflow,
    finalize_generation_workflow,
    normalize_for_execution,
)


def test_build_canonical_workflow_uses_user_delay() -> None:
    delay = FollowUpDelay(value=2, unit="hours")
    definition = build_canonical_workflow(delay)
    wait = next(s for s in definition.steps if s.type == "wait")
    assert wait.value == 2
    assert wait.unit == "hours"
    assert definition.follow_up_delay == delay
    types = [s.type for s in definition.steps]
    assert types == [
        "send_email",
        "wait",
        "reply_condition",
        "interested_branch",
        "no_reply_branch",
        "send_email",
    ]


def test_finalize_builds_no_follow_up_workflow_when_disabled() -> None:
    partial = WorkflowDefinition(
        steps=[
            WorkflowStep(id="step_1", type="send_email", name="Launch"),
            WorkflowStep(id="step_2", type="wait", days=1),
        ],
    )
    fixed = finalize_generation_workflow(partial, None, wants_follow_up=False)
    types = [s.type for s in fixed.steps]
    assert types == ["send_email", "reply_condition", "interested_branch"]
    assert fixed.follow_up_delay is None


def test_build_no_follow_up_workflow_structure() -> None:
    definition = build_no_follow_up_workflow(initial_name="Intro")
    assert definition.steps[0].name == "Intro"
    assert "wait" not in [s.type for s in definition.steps]
    assert sum(1 for s in definition.steps if s.type == "send_email") == 1


def test_finalize_repairs_invalid_llm_output() -> None:
    partial = WorkflowDefinition(
        steps=[
            WorkflowStep(id="step_1", type="send_email", name="Launch"),
            WorkflowStep(id="step_2", type="wait"),
        ],
    )
    delay = FollowUpDelay(value=3, unit="days")
    fixed = finalize_generation_workflow(partial, delay)
    assert len(fixed.steps) == 6
    assert fixed.steps[0].name == "Launch"
    wait = next(s for s in fixed.steps if s.type == "wait")
    assert wait.value == 3
    assert wait.unit == "days"


def test_normalize_for_execution_maps_generation_types() -> None:
    delay = FollowUpDelay(value=1, unit="weeks")
    definition = build_canonical_workflow(delay)
    legacy = normalize_for_execution(definition)
    types = [s.type for s in legacy.steps]
    assert "reply_condition" not in types
    assert types.count("send_email") == 2
    condition = next(s for s in legacy.steps if s.type == "condition")
    assert condition.condition == "reply_received"
    follow_up = [s for s in legacy.steps if s.type == "send_email" and s.branch == "no"]
    assert len(follow_up) == 1


def test_validate_workflow_payload_rejects_legacy_types() -> None:
    raw = {
        "steps": [
            {"id": "s1", "type": "send_email", "name": "A"},
            {"id": "s2", "type": "condition", "condition": "reply_received"},
        ],
    }
    parsed = _validate_workflow_payload(raw)
    assert len(parsed.steps) == 1
    assert parsed.steps[0].type == "send_email"


@pytest.mark.asyncio
async def test_workflow_agent_generates_and_applies_delay() -> None:
    llm = MagicMock()
    llm.generate = AsyncMock(
        return_value='{"steps":[{"id":"step_1","type":"send_email","name":"Intro"},'
        '{"id":"step_2","type":"wait"},'
        '{"id":"step_3","type":"reply_condition"},'
        '{"id":"step_4","type":"interested_branch","name":"AI Reply Agent"},'
        '{"id":"step_5","type":"no_reply_branch"},'
        '{"id":"step_6","type":"send_email","name":"Nudge"}]}',
    )
    agent = WorkflowAgent(llm=llm)
    from app.schemas.campaign import CampaignData

    campaign = CampaignData(
        product_info="Widget",
        audience="SMBs",
        tone="professional",
        cta="Book a demo",
    )
    delay = FollowUpDelay(value=7, unit="days")
    definition, reply = await agent.generate_workflow(campaign, follow_up_delay=delay)

    assert len(definition.steps) == 6
    wait = next(s for s in definition.steps if s.type == "wait")
    assert wait.value == 7
    assert wait.unit == "days"
    assert "workflow" in reply.lower() or "7" in reply
    llm.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_conversation_state_persists_workflow_to_mongo() -> None:
    workflow = build_canonical_workflow(FollowUpDelay(value=3, unit="days")).to_api_dict()
    state = {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "thread_id": "wf_abc123456789",
        "messages": [],
        "brief_approved": True,
        "workflow": workflow,
    }
    with patch(
        "app.services.persistence.conversation_repository.upsert_conversation_state",
        new_callable=AsyncMock,
    ) as upsert_conv, patch(
        "app.services.persistence.workflow_repository.upsert_workflow_definition",
        new_callable=AsyncMock,
    ) as upsert_wf:
        await save_conversation_state("user_1", "wf_abc123456789", state)

    upsert_conv.assert_awaited_once()
    upsert_wf.assert_awaited_once()
    assert upsert_wf.await_args.kwargs["workflow_definition"]["steps"]
