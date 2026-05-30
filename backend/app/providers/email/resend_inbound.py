import re

import resend

from app.core.config import settings
from app.core.logger import get_logger
from app.providers.email.base import EmailProviderError

logger = get_logger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def _html_to_plain(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_received_content(received: object) -> str | None:
    if isinstance(received, dict):
        text = received.get("text")
        html = received.get("html")
    else:
        text = getattr(received, "text", None)
        html = getattr(received, "html", None)

    if isinstance(text, str) and text.strip():
        return text.strip()
    if isinstance(html, str) and html.strip():
        return _html_to_plain(html)
    return None


async def fetch_received_email_text(email_id: str) -> str | None:
    """Fetch plain reply body from Resend Receiving API (webhooks omit body text)."""
    api_key = settings.resend_api_key.strip()
    if not api_key or not email_id.strip():
        return None

    resend.api_key = api_key
    try:
        received = await resend.Emails.Receiving.get_async(email_id.strip())
    except Exception as exc:
        logger.warning(
            "resend_receiving_fetch_failed",
            email_id=email_id,
            error=str(exc),
        )
        raise EmailProviderError(f"Resend receiving fetch failed: {exc}") from exc

    content = _extract_received_content(received)
    if content:
        return content

    logger.warning("resend_receiving_fetch_no_body", email_id=email_id)
    return None
