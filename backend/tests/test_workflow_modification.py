"""Tests for post-generation workflow modification."""

from app.schemas.follow_up_delay import FollowUpDelay
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.workflow_modification import (
    add_follow_up_to_workflow,
    apply_disable_follow_up,
    apply_enable_follow_up,
    strip_follow_up_from_workflow,
    wants_to_disable_follow_up,
    wants_to_enable_follow_up,
    workflow_has_follow_up,
)
from app.services.workflow_structure import build_canonical_workflow


def test_wants_to_disable_follow_up_detects_typos_and_remove_phrases() -> None:
    assert wants_to_disable_follow_up(
        "i do not want tios en dteh foloaup email no rmeave tahtf rom teh flow",
    )
    assert wants_to_disable_follow_up("remove the follow-up from the workflow")
    assert wants_to_disable_follow_up("no follow up needed")


def test_wants_to_disable_follow_up_ignores_unrelated_messages() -> None:
    assert not wants_to_disable_follow_up("looks good")
    assert not wants_to_disable_follow_up("change the tone to casual")


def test_strip_follow_up_from_workflow_removes_wait_and_second_email() -> None:
    delay = FollowUpDelay(value=2, unit="days")
    definition = build_canonical_workflow(delay, initial_name="Intro", follow_up_name="Nudge")

    stripped = strip_follow_up_from_workflow(definition)
    types = [s.type for s in stripped.steps]
    assert types == ["send_email", "reply_condition", "interested_branch"]
    assert stripped.follow_up_delay is None
    assert not workflow_has_follow_up(stripped)


def test_apply_disable_follow_up_updates_state_workflow() -> None:
    delay = FollowUpDelay(value=2, unit="days")
    definition = build_canonical_workflow(delay)
    state = {
        "workflow": definition.to_api_dict(),
        "wants_follow_up": True,
        "follow_up_delay": delay.to_api_dict(),
    }

    updates = apply_disable_follow_up(state)
    assert updates is not None
    assert updates["wants_follow_up"] is False
    assert updates["follow_up_delay"] is None

    workflow = updates["workflow"]
    assert isinstance(workflow, dict)
    steps = workflow["steps"]
    assert len(steps) == 3
    assert "wait" not in [s["type"] for s in steps]
    assert sum(1 for s in steps if s["type"] == "send_email") == 1


def test_wants_to_enable_follow_up_detects_add_back_with_typos() -> None:
    assert wants_to_enable_follow_up(
        "actually i make my mind againa dd teh folow uo flow but after 4 days",
    )
    assert wants_to_enable_follow_up("add the follow-up back after 4 days")
    assert not wants_to_enable_follow_up("remove the follow-up from the workflow")


def test_add_follow_up_to_workflow_restores_canonical_structure() -> None:
    stripped = build_canonical_workflow(FollowUpDelay(value=2, unit="days"))
    stripped = strip_follow_up_from_workflow(stripped)
    delay = FollowUpDelay(value=4, unit="days")

    restored = add_follow_up_to_workflow(stripped, delay)
    types = [s.type for s in restored.steps]
    assert types == [
        "send_email",
        "wait",
        "reply_condition",
        "interested_branch",
        "no_reply_branch",
        "send_email",
    ]
    wait = next(s for s in restored.steps if s.type == "wait")
    assert wait.value == 4
    assert wait.unit == "days"
    assert restored.follow_up_delay == delay


def test_apply_enable_follow_up_after_disable() -> None:
    delay = FollowUpDelay(value=2, unit="days")
    definition = build_canonical_workflow(delay)
    stripped = strip_follow_up_from_workflow(definition)
    state = {
        "workflow": stripped.to_api_dict(),
        "wants_follow_up": False,
        "follow_up_delay": None,
    }

    updates = apply_enable_follow_up(
        state,
        "actually i make my mind again add the follow up flow but after 4 days",
    )
    assert updates is not None
    assert updates["wants_follow_up"] is True
    assert updates["follow_up_delay"] == {"value": 4, "unit": "days"}

    workflow = updates["workflow"]
    assert isinstance(workflow, dict)
    steps = workflow["steps"]
    assert "wait" in [s["type"] for s in steps]
    assert sum(1 for s in steps if s["type"] == "send_email") == 2
