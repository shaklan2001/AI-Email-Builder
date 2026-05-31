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
    ) -> str:
        """Send an email to the given recipients. Returns the provider message id."""
