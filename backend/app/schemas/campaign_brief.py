from pydantic import BaseModel, Field

DEFAULT_REPLY_HANDLING = "AI Auto Reply"
DEFAULT_TOOLS_AVAILABLE: tuple[str, ...] = ("Company Information", "Demo Booking")


class CampaignBriefData(BaseModel):
    """Structured campaign brief shown before workflow generation (spec 28)."""

    campaign_name: str | None = Field(default=None, alias="campaignName")
    product_info: str | None = Field(default=None, alias="productInfo")
    audience: str | None = None
    cta: str | None = None
    tone: str | None = None
    landing_page: str | None = Field(default=None, alias="landingPage")
    image_url: str | None = Field(default=None, alias="imageUrl")
    email_length: str | None = Field(default=None, alias="emailLength")
    follow_up_enabled: str | None = Field(default=None, alias="followUpEnabled")
    follow_up_delay: str | None = Field(default=None, alias="followUpDelay")
    reply_handling: str | None = Field(default=None, alias="replyHandling")
    tools_available: list[str] = Field(
        default_factory=lambda: list(DEFAULT_TOOLS_AVAILABLE),
        alias="toolsAvailable",
    )

    model_config = {"populate_by_name": True}

    def to_api_dict(self) -> dict[str, str | list[str] | None]:
        return {
            "campaignName": self.campaign_name,
            "productInfo": self.product_info,
            "audience": self.audience,
            "cta": self.cta,
            "tone": self.tone,
            "landingPage": self.landing_page,
            "imageUrl": self.image_url,
            "emailLength": self.email_length,
            "followUpEnabled": self.follow_up_enabled,
            "followUpDelay": self.follow_up_delay,
            "replyHandling": self.reply_handling,
            "toolsAvailable": list(self.tools_available),
        }
