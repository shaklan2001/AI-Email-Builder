from abc import ABC, abstractmethod

from app.schemas.campaign import CampaignData


class LLMProviderError(Exception):
    """Raised when the LLM provider fails or returns unusable output."""


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a plain-text completion."""

    @abstractmethod
    async def extract_campaign_data(
        self,
        messages: list[dict[str, str]],
        current: CampaignData,
        *,
        revision: bool = False,
    ) -> CampaignData:
        """Extract structured campaign fields from conversation history."""
