from pydantic import BaseModel, Field


class CampaignBriefData(BaseModel):
    """Structured campaign brief shown before workflow generation."""

    campaign_name: str | None = Field(default=None, alias="campaignName")
    business_goal: str | None = Field(default=None, alias="businessGoal")
    audience: str | None = Field(default=None, alias="audience")
    product_info: str | None = Field(default=None, alias="productInfo")
    tone: str | None = None
    cta: str | None = None
    attachments: str | None = None
    landing_page: str | None = Field(default=None, alias="landingPage")
    follow_up_strategy: str | None = Field(default=None, alias="followUpStrategy")
    reply_strategy: str | None = Field(default=None, alias="replyStrategy")

    model_config = {"populate_by_name": True}

    def to_api_dict(self) -> dict[str, str | None]:
        return {
            "campaignName": self.campaign_name,
            "businessGoal": self.business_goal,
            "audience": self.audience,
            "productInfo": self.product_info,
            "tone": self.tone,
            "cta": self.cta,
            "attachments": self.attachments,
            "landingPage": self.landing_page,
            "followUpStrategy": self.follow_up_strategy,
            "replyStrategy": self.reply_strategy,
        }
