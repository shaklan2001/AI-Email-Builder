from pydantic import BaseModel, Field, model_validator


class EmailBodyVersion(BaseModel):
    subject: str = Field(..., min_length=1)
    html_content: str = Field(..., min_length=1)
    plain_text_content: str = Field(..., min_length=1)


class GeneratedEmailContent(BaseModel):
    """Tracks AI draft and user-edited final content; workflow uses final_user_version."""

    ai_generated_version: EmailBodyVersion
    final_user_version: EmailBodyVersion
    user_edited: bool = False

    @classmethod
    def from_ai_draft(
        cls,
        *,
        subject: str,
        html_content: str,
        plain_text_content: str,
    ) -> "GeneratedEmailContent":
        body = EmailBodyVersion(
            subject=subject.strip(),
            html_content=html_content.strip(),
            plain_text_content=plain_text_content.strip(),
        )
        return cls(
            ai_generated_version=body,
            final_user_version=body.model_copy(deep=True),
            user_edited=False,
        )

    @model_validator(mode="before")
    @classmethod
    def coerce_legacy_flat_email(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        if "ai_generated_version" in data or "final_user_version" in data:
            return data
        subject = data.get("subject")
        html = data.get("html_content")
        plain = data.get("plain_text_content")
        if not all(isinstance(v, str) and v.strip() for v in (subject, html, plain)):
            return data
        body = {
            "subject": str(subject).strip(),
            "html_content": str(html).strip(),
            "plain_text_content": str(plain).strip(),
        }
        return {
            "ai_generated_version": body,
            "final_user_version": body.copy(),
            "user_edited": bool(data.get("user_edited", False)),
        }

    def to_api_dict(self) -> dict[str, object]:
        final = self.final_user_version
        return {
            "subject": final.subject,
            "html_content": final.html_content,
            "plain_text_content": final.plain_text_content,
            "ai_generated_version": self.ai_generated_version.model_dump(),
            "final_user_version": self.final_user_version.model_dump(),
            "user_edited": self.user_edited,
        }
