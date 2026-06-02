import re

import resend

from app.core.config import settings
from app.core.logger import get_logger
from app.providers.email.base import EmailProvider, EmailProviderError

logger = get_logger(__name__)

_RESEND_TAG_VALUE_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")


def sanitize_resend_tag_value(value: str) -> str:
    sanitized = _RESEND_TAG_VALUE_PATTERN.sub("-", value.strip()).strip("-")
    return sanitized or "unknown"


class ResendProvider(EmailProvider):
    def __init__(self, *, api_key: str, from_email: str) -> None:
        self._api_key = api_key
        self._from_email = from_email

    async def send_email(
        self,
        *,
        subject: str,
        html_content: str,
        plain_text_content: str,
        recipients: list[str],
        reply_to: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> str:
        resend.api_key = self._api_key
        params: resend.Emails.SendParams = {
            "from": self._from_email,
            "to": recipients,
            "subject": subject,
            "html": html_content,
            "text": plain_text_content,
        }
        inbound = settings.resend_inbound_email.strip()
        resolved_reply_to = (reply_to or inbound or "").strip()
        if resolved_reply_to:
            params["reply_to"] = resolved_reply_to
        else:
            logger.warning(
                "resend_inbound_not_configured",
                detail=(
                    "RESEND_INBOUND_EMAIL is empty — Gmail Reply will go to the From "
                    "address and Resend will not receive the reply. Set your "
                    "@xxxx.resend.app address in .env."
                ),
            )
        if tags:
            params["tags"] = [
                {
                    "name": sanitize_resend_tag_value(key),
                    "value": sanitize_resend_tag_value(value),
                }
                for key, value in tags.items()
                if key.strip() and value.strip()
            ]
        try:
            response = await resend.Emails.send_async(params)
        except Exception as exc:
            raise EmailProviderError(f"Resend send failed: {exc}") from exc

        message_id = getattr(response, "id", None)
        if isinstance(response, dict):
            message_id = response.get("id")
        if not isinstance(message_id, str) or not message_id.strip():
            raise EmailProviderError("Resend returned no message id")
        return message_id.strip()


def get_resend_provider() -> ResendProvider:
    api_key = settings.resend_api_key.strip()
    if not api_key:
        raise EmailProviderError("RESEND_API_KEY is not configured")
    from_email = settings.resend_from_email.strip()
    if not from_email:
        raise EmailProviderError("RESEND_FROM_EMAIL is not configured")
    return ResendProvider(api_key=api_key, from_email=from_email)
