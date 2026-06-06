from app.providers.email.resend_provider import sanitize_resend_tag_value


def test_sanitize_resend_tag_value_preserves_valid_chars() -> None:
    assert sanitize_resend_tag_value("wf_a957f4dc8f6a") == "wf_a957f4dc8f6a"


def test_sanitize_resend_tag_value_strips_email_chars() -> None:
    assert (
        sanitize_resend_tag_value("nishant.ns171@gmail.com")
        == "nishant-ns171-gmail-com"
    )
