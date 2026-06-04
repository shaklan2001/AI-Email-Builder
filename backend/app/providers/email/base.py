from abc import ABC, abstractmethod


class EmailProviderError(Exception):
    """Raised when the email provider fails or is misconfigured."""


class EmailProvider(ABC):
    @abstractmethod
    async def send_email(
        self,
        *,
        subject: str,
        html_content: str,
        plain_text_content: str,
        recipients: list[str],
        workflow_id: str | None = None,
        lead_id: str | None = None,
    ) -> str:
        """Send an email. Returns the provider message id (one id per API call)."""
