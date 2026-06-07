"""Brief approval detection from chat messages."""

from app.services.brief_actions import is_brief_approval_message, parse_brief_user_action


def test_exact_looks_good_approves() -> None:
    assert parse_brief_user_action("Looks Good") == "approve"
    assert is_brief_approval_message("looks good to me")


def test_informal_and_typo_approval_phrases() -> None:
    assert is_brief_approval_message("noy it look good")
    assert is_brief_approval_message("now it looks good")
    assert is_brief_approval_message("ok it looks good")
    assert is_brief_approval_message("yes looks good")
    assert is_brief_approval_message("good to go")


def test_edit_action_still_detected() -> None:
    assert parse_brief_user_action("Edit Campaign Details") == "edit"


def test_casual_approval_phrases() -> None:
    assert is_brief_approval_message("everything look cool")
    assert is_brief_approval_message("everything looks good")
    assert is_brief_approval_message("all set")
