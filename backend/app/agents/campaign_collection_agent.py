"""Production LangGraph agent: collect campaign information through conversation."""

from __future__ import annotations

from dataclasses import dataclass

from app.langgraph.state import CampaignState, apply_campaign_data, campaign_data_from_state
from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.repositories.workflow_repository import workflow_repository
from app.schemas.campaign import CampaignData
from app.schemas.follow_up_delay import FollowUpDelay
from app.services.campaign_extraction import extract_from_latest_user_message
from app.services.campaign_field_policy import (
    DEFAULT_FOLLOW_UP_DELAY,
    EMAIL_LENGTH_FIELD,
    FOLLOW_UP_DELAY_FIELD,
    WANTS_FOLLOW_UP_FIELD,
    apply_field_defaults,
    compute_collection_missing_fields,
    infer_product_from_minimal_message,
    is_proceed_message,
    is_skip_message,
    mark_all_optional_skipped,
    next_field_to_collect,
    normalize_skipped_fields,
    resolve_skip_for_field,
)
from app.services.collection_preferences import (
    default_email_length,
    parse_email_length_detail,
    parse_wants_follow_up,
)
from app.services.campaign_revision import (
    campaign_changed,
    is_material_change,
    should_overwrite_campaign_fields,
    stale_artifact_reset,
)
from app.services.conversation_response import (
    build_collection_reply,
    build_product_required_after_skip,
)
from app.services.follow_up_delay import follow_up_delay_from_state, parse_follow_up_delay


@dataclass
class CampaignCollectionTurnResult:
    state_updates: dict[str, object]
    assistant_reply: str | None = None


class CampaignCollectionAgent:
    """Extracts campaign fields, handles skip/delegate, tracks missing_fields, asks one question."""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        return get_groq_provider()

    @staticmethod
    def _latest_user_message(messages: list[dict[str, str]]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "").strip()
        return ""

    async def extract_and_update(self, state: CampaignState) -> dict[str, object]:
        """Analyze latest message, merge extractions, apply skip/delegate, return state patches."""
        llm = self._get_llm()
        before = campaign_data_from_state(state)
        messages = list(state.get("messages") or [])
        latest = self._latest_user_message(messages)
        revision = should_overwrite_campaign_fields(
            latest,
            brief_status=state.get("brief_status"),
        )
        skipped = normalize_skipped_fields(state.get("skipped_fields"))
        editing_brief = state.get("brief_status") == "editing"

        current = extract_from_latest_user_message(messages, before, revision=revision)
        extracted = await llm.extract_campaign_data(messages, current, revision=revision)
        merged = current.merge(extracted, revision=revision)
        merged = extract_from_latest_user_message(messages, merged, revision=revision)

        minimal_product = infer_product_from_minimal_message(latest)
        if minimal_product and not merged.product_info:
            merged = merged.apply_updates({"product_info": minimal_product})

        updates_delay: dict[str, object] = {}
        updates_prefs: dict[str, object] = {}
        current_wants_follow_up = state.get("wants_follow_up")
        current_email_length = state.get("email_length")

        next_ask = next_field_to_collect(
            merged,
            skipped,
            include_optional=editing_brief,
            follow_up_delay=state.get("follow_up_delay"),
            wants_follow_up=current_wants_follow_up,
            email_length=current_email_length,
        )

        if is_skip_message(latest) and next_ask == EMAIL_LENGTH_FIELD:
            updates_prefs["email_length"] = default_email_length()
            skipped.add(EMAIL_LENGTH_FIELD)
        elif is_skip_message(latest) and next_ask == WANTS_FOLLOW_UP_FIELD:
            updates_prefs["wants_follow_up"] = False
            updates_prefs["follow_up_delay"] = None
            skipped.add(WANTS_FOLLOW_UP_FIELD)
        elif is_skip_message(latest) and next_ask == FOLLOW_UP_DELAY_FIELD:
            delay = DEFAULT_FOLLOW_UP_DELAY
            updates_delay["follow_up_delay"] = delay.to_api_dict()
            skipped.add(FOLLOW_UP_DELAY_FIELD)
        elif is_skip_message(latest) and next_ask:
            skipped, patches = resolve_skip_for_field(next_ask, skipped)
            merged = merged.apply_updates(patches)
        elif is_skip_message(latest) or is_proceed_message(latest):
            skipped = mark_all_optional_skipped(skipped)

        merged = apply_field_defaults(merged, skipped)

        parsed_length = parse_email_length_detail(latest)
        if parsed_length is not None and (
            next_ask == EMAIL_LENGTH_FIELD or state.get("brief_status") == "editing"
        ):
            updates_prefs["email_length"] = parsed_length.category
            if parsed_length.words is not None:
                updates_prefs["email_length_words"] = parsed_length.words
            skipped.discard(EMAIL_LENGTH_FIELD)

        parsed_wants_follow_up = parse_wants_follow_up(latest)
        if parsed_wants_follow_up is not None and next_ask == WANTS_FOLLOW_UP_FIELD:
            updates_prefs["wants_follow_up"] = parsed_wants_follow_up
            if not parsed_wants_follow_up:
                updates_prefs["follow_up_delay"] = None

        parsed_delay = parse_follow_up_delay(latest)
        if parsed_delay is not None and next_ask == FOLLOW_UP_DELAY_FIELD:
            updates_delay["follow_up_delay"] = parsed_delay.to_api_dict()

        updates: dict[str, object] = dict(apply_campaign_data(state, merged))
        updates.update(updates_prefs)
        updates.update(updates_delay)

        rule_updates = extract_from_latest_user_message(messages, before, revision=revision)
        for field in CampaignData.model_fields:
            before_val = getattr(before, field)
            after_val = getattr(rule_updates, field)
            if after_val and str(after_val).strip() and after_val != before_val:
                skipped.discard(field)

        updates["skipped_fields"] = sorted(skipped)

        if merged.campaign_name:
            updates["campaign_name"] = merged.campaign_name
            workflow_id = state.get("workflow_id") or ""
            user_id = state.get("user_id") or ""
            if workflow_id and user_id:
                await workflow_repository.update_name(
                    user_id=user_id,
                    workflow_id=workflow_id,
                    name=merged.campaign_name,
                )

        if campaign_changed(before, merged) and (
            revision or is_material_change(before, merged) or state.get("brief_approved")
        ):
            updates.update(
                stale_artifact_reset(clear_brief=revision or is_material_change(before, merged)),
            )

        if not state.get("brief_approved") and "workflow" not in updates:
            updates["workflow"] = None

        draft_state: CampaignState = {**state, **updates}  # type: ignore[misc]
        updates["missing_fields"] = compute_collection_missing_fields(draft_state)
        return updates

    def missing_fields_snapshot(self, state: CampaignState) -> dict[str, object]:
        return {"missing_fields": compute_collection_missing_fields(state)}

    def build_next_question(
        self,
        state: CampaignState,
        *,
        post_generation: bool = False,
    ) -> str:
        if post_generation:
            raise ValueError("use LLM reply path for post-generation mode")

        campaign = campaign_data_from_state(state)
        skipped = normalize_skipped_fields(state.get("skipped_fields"))
        campaign = apply_field_defaults(campaign, skipped)
        messages = list(state.get("messages") or [])
        latest = self._latest_user_message(messages)
        editing_brief = state.get("brief_status") == "editing"

        if is_skip_message(latest) and not campaign.product_info:
            return build_product_required_after_skip()

        return build_collection_reply(
            campaign,
            editing_brief=editing_brief,
            skipped_fields=skipped,
            follow_up_delay=state.get("follow_up_delay"),
            wants_follow_up=state.get("wants_follow_up"),
            email_length=state.get("email_length"),
            email_length_words=state.get("email_length_words"),
        )

    async def process_discovery_turn(self, state: CampaignState) -> CampaignCollectionTurnResult:
        """Full discovery turn: extract, refresh missing_fields, produce strategist reply."""
        updates = await self.extract_and_update(state)
        merged_state: CampaignState = {**state, **updates}  # type: ignore[misc]
        reply = self.build_next_question(merged_state)
        updates["assistant_reply"] = reply
        return CampaignCollectionTurnResult(state_updates=updates, assistant_reply=reply)


campaign_collection_agent = CampaignCollectionAgent()
