"""Routing from collection to campaign brief approval."""

from app.langgraph.nodes import route_after_missing_information
from app.langgraph.state import ConversationState
from app.services.campaign_field_policy import (
    EMAIL_LENGTH_FIELD,
    FOLLOW_UP_DELAY_FIELD,
    WANTS_FOLLOW_UP_FIELD,
)


def _ready_state() -> ConversationState:
    return {
        "workflow_id": "wf_abc123456789",
        "user_id": "user_1",
        "messages": [],
        "product_info": "Freelance Mobile & Web Development",
        "campaign_name": "Webbuilder Email Campaign",
        "audience": "General Customers",
        "email_length": "medium",
        "wants_follow_up": True,
        "wants_cta": True,
        "cta": "Learn More",
        "landing_page": "https://www.example.com/",
        "follow_up_delay": {"value": 5, "unit": "minutes"},
        "skipped_fields": [
            EMAIL_LENGTH_FIELD,
            WANTS_FOLLOW_UP_FIELD,
            FOLLOW_UP_DELAY_FIELD,
            "campaign_name",
            "audience",
            "wants_cta",
            "cta",
            "landing_page",
        ],
    }


def test_routes_to_campaign_brief_when_optional_assets_missing() -> None:
    state = _ready_state()
    assert route_after_missing_information(state) == "campaign_brief"


def test_routes_to_question_generator_while_editing_optional_fields() -> None:
    state = _ready_state()
    state["brief_status"] = "editing"
    state["skipped_fields"] = [
        EMAIL_LENGTH_FIELD,
        WANTS_FOLLOW_UP_FIELD,
        FOLLOW_UP_DELAY_FIELD,
        "campaign_name",
        "audience",
        "wants_cta",
        "cta",
        "landing_page",
    ]
    assert route_after_missing_information(state) == "question_generator"
