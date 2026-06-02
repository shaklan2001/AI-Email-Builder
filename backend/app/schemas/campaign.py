from pydantic import BaseModel, Field


class CampaignData(BaseModel):
    """Structured campaign fields extracted from conversation."""

    campaign_name: str | None = None
    business_goal: str | None = None
    product_info: str | None = None
    audience: str | None = None
    tone: str | None = None
    cta: str | None = None
    landing_page: str | None = None
    product_image: str | None = None
    attachments: str | None = None
    competitors: str | None = None

    def merge(self, other: "CampaignData", *, revision: bool = False) -> "CampaignData":
        """Merge extracted fields. Revision mode overwrites with non-empty values from other."""
        data = self.model_dump()
        for field in CampaignData.model_fields:
            other_val = getattr(other, field)
            if not other_val or not str(other_val).strip():
                continue
            if revision or not data.get(field):
                data[field] = str(other_val).strip()
        return CampaignData.model_validate(data)

    def apply_updates(self, updates: dict[str, str | None]) -> "CampaignData":
        """Apply explicit user corrections (overwrites and clears allowed)."""
        data = self.model_dump()
        for field, value in updates.items():
            if field not in CampaignData.model_fields:
                continue
            if value is None:
                data[field] = None
            elif str(value).strip():
                data[field] = str(value).strip()
        return CampaignData.model_validate(data)

    def missing_fields(self) -> list[str]:
        """Only Product / Service is required for campaign setup."""
        from app.services.campaign_field_policy import missing_required_fields

        return missing_required_fields(self)

    def has_required_for_workflow(self) -> bool:
        """True when product/service is known — optional fields may use defaults."""
        return not self.missing_fields()

    def has_required_for_workflow_with_delay(
        self,
        follow_up_delay: object = None,
        *,
        wants_follow_up: object = None,
        email_length: object = None,
    ) -> bool:
        """True when product, email length, follow-up preference, and delay (if needed) are set."""
        from app.services.campaign_field_policy import is_ready_for_campaign_brief

        return is_ready_for_campaign_brief(
            self,
            follow_up_delay=follow_up_delay,
            wants_follow_up=wants_follow_up,
            email_length=email_length,
        )

    def filled_summary(self) -> str:
        lines: list[str] = []
        labels = {
            "campaign_name": "Campaign Name",
            "product_info": "Product",
            "audience": "Audience",
            "business_goal": "Goal",
            "tone": "Tone",
            "cta": "CTA",
            "landing_page": "Landing Page",
            "product_image": "Images",
            "attachments": "Attachments",
            "competitors": "Competitors",
        }
        for key, label in labels.items():
            value = getattr(self, key)
            if value and str(value).strip():
                lines.append(f"- {label}: {value}")
        return "\n".join(lines) if lines else "None collected yet."

    def authoritative_summary(self) -> str:
        """Canonical campaign block for workflow and email generation (no chat history)."""
        return (
            "AUTHORITATIVE CAMPAIGN BRIEF (use only these values — ignore older topics):\n"
            f"{self.filled_summary()}"
        )

    def email_generation_context(self) -> str:
        """Inputs for the email generation agent (product, audience, CTA, website, image, tone)."""
        lines: list[str] = ["CAMPAIGN INPUTS FOR EMAIL GENERATION:"]
        fields: tuple[tuple[str, str], ...] = (
            ("campaign_name", "Campaign / Company Name"),
            ("business_goal", "Business Goal"),
            ("product_info", "Product"),
            ("audience", "Audience"),
            ("cta", "CTA"),
            ("landing_page", "Website"),
            ("product_image", "Image URL"),
            ("tone", "Tone"),
        )
        for key, label in fields:
            value = getattr(self, key, None)
            if value and str(value).strip():
                lines.append(f"- {label}: {value}")
        if len(lines) == 1:
            lines.append("- (no campaign inputs collected yet)")
        return "\n".join(lines)
