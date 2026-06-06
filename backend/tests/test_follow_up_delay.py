"""Tests for configurable follow-up delay (spec 26)."""

import pytest

from app.schemas.follow_up_delay import FollowUpDelay
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.campaign_field_policy import (
    EMAIL_LENGTH_FIELD,
    FOLLOW_UP_DELAY_FIELD,
    is_ready_for_campaign_brief,
    next_field_to_collect,
)
from app.services.conversation_response import build_collection_reply
from app.services.follow_up_delay import (
    FOLLOW_UP_DELAY_QUESTION,
    apply_follow_up_delay_to_workflow,
    format_wait_label,
    parse_follow_up_delay,
)
from app.schemas.campaign import CampaignData


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("4 hours", FollowUpDelay(value=4, unit="hours")),
        ("1 day", FollowUpDelay(value=1, unit="days")),
        ("3 Days", FollowUpDelay(value=3, unit="days")),
        ("7 days please", FollowUpDelay(value=7, unit="days")),
        ("2 weeks", FollowUpDelay(value=2, unit="weeks")),
    ],
)
def test_parse_follow_up_delay(text: str, expected: FollowUpDelay) -> None:
    assert parse_follow_up_delay(text) == expected


def test_format_wait_label() -> None:
    assert format_wait_label(FollowUpDelay(value=3, unit="days")) == "Wait 3 Days"
    assert format_wait_label(FollowUpDelay(value=4, unit="hours")) == "Wait 4 Hours"
    assert format_wait_label(FollowUpDelay(value=1, unit="weeks")) == "Wait 1 Week"


def test_next_field_after_product_is_email_length() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    assert next_field_to_collect(campaign, set(), follow_up_delay=None) == EMAIL_LENGTH_FIELD


def test_is_ready_for_brief_requires_follow_up_preferences() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    assert not is_ready_for_campaign_brief(campaign, follow_up_delay=None)
    assert not is_ready_for_campaign_brief(
        campaign,
        email_length="medium",
        wants_follow_up=True,
        follow_up_delay=None,
    )
    delay = {"value": 3, "unit": "days"}
    assert is_ready_for_campaign_brief(
        campaign,
        email_length="medium",
        wants_follow_up=True,
        follow_up_delay=delay,
    )
    assert is_ready_for_campaign_brief(
        campaign,
        email_length="medium",
        wants_follow_up=False,
        follow_up_delay=None,
    )


def test_collection_reply_asks_follow_up_timing_when_enabled() -> None:
    campaign = CampaignData(product_info="Acme Widgets")
    reply = build_collection_reply(
        campaign,
        email_length="medium",
        wants_follow_up=True,
        follow_up_delay=None,
    )
    assert FOLLOW_UP_DELAY_QUESTION.split("\n")[0] in reply


def test_apply_follow_up_delay_to_workflow() -> None:
    definition = WorkflowDefinition(
        steps=[
            WorkflowStep(id="s1", type="send_email", name="Initial"),
            WorkflowStep(id="s2", type="wait", days=1),
            WorkflowStep(id="s3", type="reply_condition"),
        ],
    )
    delay = FollowUpDelay(value=4, unit="hours")
    updated = apply_follow_up_delay_to_workflow(definition, delay)
    assert updated.follow_up_delay == delay
    wait_step = next(s for s in updated.steps if s.type == "wait")
    assert wait_step.value == 4
    assert wait_step.unit == "hours"
