import json
import re

from groq import AsyncGroq, GroqError
from langsmith import traceable

from app.core.config import settings
from app.core.langsmith_usage import record_llm_token_usage
from app.providers.llm.base import LLMProvider, LLMProviderError
from app.schemas.campaign import CampaignData
from app.services.campaign_field_policy import condense_product_info, is_vague_product_info

_EXTRACTION_SYSTEM = """You are a sales and marketing campaign strategist.
Extract campaign information from the conversation.
Return ONLY valid JSON with these keys (use null for unknown):
campaign_name, business_goal, product_info, audience, tone, cta, landing_page, product_image, attachments, competitors

Rules:
- If the user says skip, none, don't know, not sure, no preference, doesn't matter, recommend for me, anything works, or you decide for a field, leave that field null.
- Only product_info is strictly required; other fields may be omitted.
- campaign_name: short dashboard title (2–6 words) — infer from product/goal when the user did not name the campaign
- landing_page: website or landing URL only — never set this when the user only mentions an image URL
- product_image: product image URL when the user shares a picture or image link (including product page links used as images)
- audience: summarize target audience (e.g. "Age 16–35")
- product_info: SHORT product or service name only (2–6 words). When the user describes their business in a sentence, extract only the service label (e.g. "Freelance Mobile Development") — not the full message. Put who they want to reach in audience.
- Leave product_info null for vague phrases like "new product", "my product", or "a service"
Do not include markdown or explanation."""

_EXTRACTION_REVISION_SYSTEM = """You are a sales and marketing campaign strategist.
The user's LATEST message revises or replaces earlier campaign details.
Return ONLY valid JSON with these keys (use null for fields not changed in the latest message):
campaign_name, business_goal, product_info, audience, tone, cta, landing_page, product_image, attachments, competitors

Rules:
- Use ONLY the latest user message for changes — do NOT keep outdated products (e.g. AirPure) if the user switched campaigns.
- Non-null values REPLACE previous campaign data for that field.
- landing_page is the website URL only; product_image is the email/poster image URL only
- If the user only wants an image URL updated, change product_image only — do not change landing_page
- Do not store vague product names like "new product" or "my product" — leave product_info null instead
Do not include markdown or explanation."""

def _parse_json_object(text: str) -> dict[str, object]:
    cleaned = text.strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
    if fence:
        try:
            parsed = json.loads(fence.group(1).strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    brace = re.search(r"\{[\s\S]*\}", cleaned)
    if brace:
        try:
            parsed = json.loads(brace.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {}


def _validate_campaign_payload(raw: dict[str, object]) -> CampaignData:
    normalized: dict[str, str | None] = {}
    for field in CampaignData.model_fields:
        value = raw.get(field)
        if value is None:
            normalized[field] = None
        elif isinstance(value, str):
            stripped = value.strip()
            normalized[field] = stripped or None
        else:
            normalized[field] = str(value).strip() or None
    condensed = condense_product_info(normalized.get("product_info"))
    if condensed is None or is_vague_product_info(condensed):
        normalized["product_info"] = None
    else:
        normalized["product_info"] = condensed
    try:
        return CampaignData.model_validate(normalized)
    except Exception:
        return CampaignData()


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    @traceable(run_type="llm", name="groq_chat_completion")
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
        except GroqError as exc:
            raise LLMProviderError(f"Groq request failed: {exc}") from exc

        record_llm_token_usage(getattr(response, "usage", None))

        content = response.choices[0].message.content
        if not content or not content.strip():
            raise LLMProviderError("Groq returned an empty response")
        return content.strip()

    @traceable(run_type="chain", name="extract_campaign_data")
    async def extract_campaign_data(
        self,
        messages: list[dict[str, str]],
        current: CampaignData,
        *,
        revision: bool = False,
    ) -> CampaignData:
        latest_user = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                latest_user = message.get("content", "").strip()
                break

        if revision and latest_user:
            system = _EXTRACTION_REVISION_SYSTEM
            user_prompt = (
                f"Current campaign (may be outdated):\n{current.filled_summary()}\n\n"
                f"LATEST USER MESSAGE:\n{latest_user}\n\n"
                "Return updated fields from the latest message only."
            )
        else:
            system = _EXTRACTION_SYSTEM
            history = "\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages[-20:]
            )
            user_prompt = (
                f"Known campaign data:\n{current.filled_summary()}\n\n"
                f"Conversation:\n{history}\n\n"
                "Update extraction from the conversation. Prefer the most recent user intent."
            )

        try:
            raw_text = await self.generate(system, user_prompt)
        except LLMProviderError:
            return current

        extracted = _validate_campaign_payload(_parse_json_object(raw_text))
        return current.merge(extracted, revision=revision)


def get_groq_provider() -> GroqProvider:
    if not settings.groq_api_key:
        raise LLMProviderError("GROQ_API_KEY is not configured")
    return GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)
