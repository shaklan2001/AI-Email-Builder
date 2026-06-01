import resend

from app.core.config import settings
from app.providers.email.base import EmailProvider, EmailProviderError


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
    ) -> str:
        resend.api_key = self._api_key
        params: resend.Emails.SendParams = {
            "from": self._from_email,
            "to": recipients,
            "subject": subject,
            "html": html_content,
            "text": plain_text_content,
        }
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
