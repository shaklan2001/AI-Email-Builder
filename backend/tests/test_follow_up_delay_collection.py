"""Collection flow asks follow-up preference before delay (spec 26)."""

from app.schemas.campaign import CampaignData
from app.services.campaign_field_policy import FOLLOW_UP_DELAY_FIELD, WANTS_FOLLOW_UP_FIELD
from app.services.conversation_response import _follow_up_question


def test_follow_up_preference_question_text() -> None:
    reply = _follow_up_question(WANTS_FOLLOW_UP_FIELD)
    assert "should I send a follow-up email" in reply


def test_follow_up_delay_question_text() -> None:
    reply = _follow_up_question(FOLLOW_UP_DELAY_FIELD)
    assert "If a recipient does not reply, when should I send the follow-up?" in reply
    assert "4 Hours" in reply
    assert "2 Weeks" in reply
