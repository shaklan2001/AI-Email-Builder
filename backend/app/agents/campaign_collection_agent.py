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
    CTA_LABEL_FIELD,
    CTA_URL_FIELD,
    EMAIL_LENGTH_FIELD,
    FOLLOW_UP_DELAY_FIELD,
    WANTS_CTA_FIELD,
    WANTS_FOLLOW_UP_FIELD,
    apply_field_defaults,
    compute_collection_missing_fields,
    fill_missing_preference_defaults,
    has_email_length,
    has_cta_content,
    has_wants_follow_up,
    infer_product_from_minimal_message,
    infer_wants_cta_from_campaign,
    is_declining_tweaks_message,
    is_acknowledgement_message,
    is_delegate_message,
    is_hard_skip_message,
    infer_cta_label_from_message,
    is_no_cta_message,
    is_proceed_message,
    parse_cta_label,
    parse_wants_cta,
    is_skip_message,
    is_vague_product_info,
    mark_all_optional_skipped,
    next_field_to_collect,
    normalize_skipped_fields,
    preference_default_updates,
    resolve_skip_for_field,
    should_default_preference_field,
)
from app.services.collection_preferences import (
    follow_up_prefs_from_brief_dict,
    parse_email_length_detail,
    parse_wants_follow_up,
)
from app.services.workflow_modification import (
    resolve_follow_up_delay_for_edit,
    wants_to_disable_follow_up,
    wants_to_enable_follow_up,
)
from app.services.brief_actions import is_brief_approval_message
from app.services.campaign_revision import (
    campaign_changed,
    is_material_change,
    should_overwrite_campaign_fields,
    stale_artifact_reset,
)
from app.services.campaign_naming import (
    is_placeholder_campaign_name,
    resolve_campaign_display_name,
)
from app.services.campaign_state import hydrate_campaign_from_brief
from app.services.conversation_response import (
    BRIEF_REPLY_SYSTEM,
    BRIEF_UPDATE_REPLY_SYSTEM,
    COLLECTION_REPLY_SYSTEM,
    build_brief_reply_context,
    build_collection_fallback_reply,
    build_collection_prompt_context,
    build_product_required_after_skip,
)
from app.services.follow_up_delay import (
    follow_up_delay_from_state,
    infer_follow_up_delay_from_messages,
    is_affirmation_message,
    parse_follow_up_delay,
)


@dataclass
class CampaignCollectionTurnResult:
    state_updates: dict[str, object]
    assistant_reply: str | None = None


@dataclass
class _PreferencePatch:
    prefs: dict[str, object]
    delay: dict[str, object]
    skipped: set[str]
    merged: CampaignData | None = None


def _is_short_preference_answer(text: str) -> bool:
    return len(text.strip().split()) <= 6


def _merge_preference_patches(
    target_prefs: dict[str, object],
    target_delay: dict[str, object],
    skipped: set[str],
    patch: _PreferencePatch,
    merged: CampaignData,
) -> tuple[CampaignData, set[str]]:
    target_prefs.update(patch.prefs)
    target_delay.update(patch.delay)
    skipped |= patch.skipped
    if patch.merged is not None:
        merged = patch.merged
    return merged, skipped


class CampaignCollectionAgent:
    """Extracts campaign fields, handles skip/delegate, tracks missing_fields, asks one question."""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        return get_groq_provider()

    async def ensure_workflow_display_name(
        self,
        state: CampaignState,
        campaign: CampaignData,
    ) -> dict[str, object]:
        """Ensure Mongo workflow title and state campaign_name are set before generation."""
        resolved = await self._maybe_auto_name_campaign(state, campaign)
        if not resolved:
            return {}

        workflow_id = state.get("workflow_id") or ""
        user_id = state.get("user_id") or ""
        if workflow_id and user_id:
            await workflow_repository.update_name(
                user_id=user_id,
                workflow_id=workflow_id,
                name=resolved,
            )
        return {"campaign_name": resolved}

    async def _maybe_auto_name_campaign(
        self,
        state: CampaignState,
        campaign: CampaignData,
    ) -> str | None:
        """Generate a dashboard title when product is known and the name is still a placeholder."""
        if not campaign.product_info or is_vague_product_info(campaign.product_info):
            return None
        if campaign.campaign_name and not is_placeholder_campaign_name(campaign.campaign_name):
            return campaign.campaign_name

        state_name = state.get("campaign_name")
        if isinstance(state_name, str) and not is_placeholder_campaign_name(state_name):
            return state_name.strip()

        record_name: str | None = None
        workflow_id = state.get("workflow_id") or ""
        user_id = state.get("user_id") or ""
        if workflow_id and user_id:
            try:
                record = await workflow_repository.get_by_id(user_id, workflow_id)
            except RuntimeError:
                record = None
            if record is not None:
                record_name = record.name

        if record_name and not is_placeholder_campaign_name(record_name):
            return record_name.strip()

        return await resolve_campaign_display_name(
            llm=self._get_llm(),
            campaign=campaign,
            state_name=state_name if isinstance(state_name, str) else None,
            record_name=record_name,
        )

    @staticmethod
    def _latest_user_message(messages: list[dict[str, str]]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "").strip()
        return ""

    @staticmethod
    def _apply_brief_follow_up_prefs(
        brief: object,
        wants_follow_up: object,
        resolved_delay: FollowUpDelay | None,
    ) -> tuple[object, FollowUpDelay | None]:
        if not isinstance(brief, dict):
            return wants_follow_up, resolved_delay

        brief_wants, brief_delay = follow_up_prefs_from_brief_dict(brief)
        if brief_wants is True:
            wants_follow_up = True
            if brief_delay is not None:
                resolved_delay = brief_delay
        elif brief_wants is False and wants_follow_up is not True:
            wants_follow_up = False
            resolved_delay = None
        return wants_follow_up, resolved_delay

    @staticmethod
    def _default_follow_up_delay_for_approval(
        wants_follow_up: object,
        resolved_delay: FollowUpDelay | None,
        messages: list[dict[str, str]],
    ) -> FollowUpDelay | None:
        if wants_follow_up is True and resolved_delay is None:
            return infer_follow_up_delay_from_messages(messages) or DEFAULT_FOLLOW_UP_DELAY
        return resolved_delay

    @staticmethod
    def _build_follow_up_approval_prefs(
        wants_follow_up: object,
        resolved_delay: FollowUpDelay | None,
        state: CampaignState,
    ) -> dict[str, object]:
        prefs: dict[str, object] = {}
        if isinstance(wants_follow_up, bool):
            prefs["wants_follow_up"] = wants_follow_up
        elif wants_follow_up is None:
            default_prefs, default_delay, _ = fill_missing_preference_defaults(
                email_length=state.get("email_length"),
                wants_follow_up=None,
                follow_up_delay=state.get("follow_up_delay"),
                delegate=True,
            )
            prefs.update(default_prefs)
            if default_delay:
                prefs.update(default_delay)

        if wants_follow_up is False:
            prefs["follow_up_delay"] = None
        elif resolved_delay is not None:
            prefs["follow_up_delay"] = resolved_delay.to_api_dict()
        return prefs

    @staticmethod
    def _resolve_follow_up_for_approval(state: CampaignState) -> dict[str, object]:
        """Ensure follow-up prefs match the approved brief before workflow generation."""
        messages = list(state.get("messages") or [])
        wants_follow_up = state.get("wants_follow_up")
        resolved_delay = follow_up_delay_from_state(state.get("follow_up_delay"))

        wants_follow_up, resolved_delay = CampaignCollectionAgent._apply_brief_follow_up_prefs(
            state.get("campaign_brief"),
            wants_follow_up,
            resolved_delay,
        )
        resolved_delay = CampaignCollectionAgent._default_follow_up_delay_for_approval(
            wants_follow_up,
            resolved_delay,
            messages,
        )
        return CampaignCollectionAgent._build_follow_up_approval_prefs(
            wants_follow_up,
            resolved_delay,
            state,
        )

    @staticmethod
    def _approval_state_patch(state: CampaignState) -> dict[str, object]:
        """Preserve approved brief fields — do not re-extract or invalidate on approval."""
        hydrated = hydrate_campaign_from_brief(state)
        updates: dict[str, object] = dict(apply_campaign_data(state, hydrated))
        updates.update(CampaignCollectionAgent._resolve_follow_up_for_approval(state))
        prefs, delay, skip = fill_missing_preference_defaults(
            email_length=state.get("email_length"),
            wants_follow_up=updates.get("wants_follow_up", state.get("wants_follow_up")),
            follow_up_delay=updates.get("follow_up_delay", state.get("follow_up_delay")),
            delegate=True,
        )
        updates.update(prefs)
        updates.update(delay)
        if state.get("email_length") is not None:
            updates["email_length"] = state.get("email_length")
        if state.get("email_length_words") is not None:
            updates["email_length_words"] = state.get("email_length_words")
        skipped = normalize_skipped_fields(state.get("skipped_fields")) | skip
        updates["skipped_fields"] = sorted(skipped)
        draft_state: CampaignState = {**state, **updates}  # type: ignore[misc]
        updates["missing_fields"] = compute_collection_missing_fields(draft_state)
        return updates

    @staticmethod
    def _normalize_merged_product_info(
        merged: CampaignData,
        state: CampaignState,
        latest: str,
    ) -> CampaignData:
        minimal_product = infer_product_from_minimal_message(latest)
        if minimal_product and not merged.product_info:
            merged = merged.apply_updates({"product_info": minimal_product})

        hydrated = hydrate_campaign_from_brief(state)
        has_usable_hydrated = (
            hydrated.product_info and not is_vague_product_info(hydrated.product_info)
        )
        if (
            (not merged.product_info or is_vague_product_info(merged.product_info))
            and has_usable_hydrated
        ):
            merged = merged.apply_updates({"product_info": hydrated.product_info})

        if is_vague_product_info(merged.product_info):
            merged = merged.apply_updates({"product_info": None})
        return merged

    @staticmethod
    def _preference_default_patch(next_ask: str | None, latest: str) -> _PreferencePatch | None:
        field_handlers = (
            (
                EMAIL_LENGTH_FIELD,
                lambda: preference_default_updates(
                    EMAIL_LENGTH_FIELD,
                    delegate=is_delegate_message(latest) or is_acknowledgement_message(latest),
                ),
            ),
            (
                WANTS_FOLLOW_UP_FIELD,
                lambda: preference_default_updates(
                    WANTS_FOLLOW_UP_FIELD,
                    delegate=not is_hard_skip_message(latest),
                ),
            ),
            (
                FOLLOW_UP_DELAY_FIELD,
                lambda: preference_default_updates(FOLLOW_UP_DELAY_FIELD, delegate=True),
            ),
            (
                WANTS_CTA_FIELD,
                lambda: preference_default_updates(
                    WANTS_CTA_FIELD,
                    delegate=not is_hard_skip_message(latest),
                ),
            ),
            (
                CTA_LABEL_FIELD,
                lambda: preference_default_updates(
                    CTA_LABEL_FIELD,
                    delegate=is_delegate_message(latest) or is_acknowledgement_message(latest),
                ),
            ),
        )
        for field, build_defaults in field_handlers:
            if next_ask == field and should_default_preference_field(latest, field):
                prefs, delay, skip = build_defaults()
                return _PreferencePatch(dict(prefs), dict(delay), set(skip))
        return None

    @staticmethod
    def _wants_cta_patch(
        latest: str,
        next_ask: str | None,
        merged: CampaignData,
        skipped: set[str],
    ) -> _PreferencePatch | None:
        if next_ask != WANTS_CTA_FIELD:
            return None

        if has_cta_content(merged):
            return _PreferencePatch(
                {"wants_cta": True},
                {},
                skipped | {WANTS_CTA_FIELD},
                merged,
            )

        parsed_wants = parse_wants_cta(latest, campaign=merged)
        label = infer_cta_label_from_message(latest, campaign=merged) or parse_cta_label(latest)

        if parsed_wants is False:
            return _PreferencePatch(
                {"wants_cta": False},
                {},
                skipped | {WANTS_CTA_FIELD, CTA_LABEL_FIELD},
                merged.apply_updates({"cta": None}),
            )

        if parsed_wants is True or label:
            new_skipped = skipped | {WANTS_CTA_FIELD}
            merged_update = merged
            prefs: dict[str, object] = {"wants_cta": True}
            if label:
                merged_update = merged.apply_updates({"cta": label})
                prefs["cta"] = label
                new_skipped |= {CTA_LABEL_FIELD}
            return _PreferencePatch(prefs, {}, new_skipped, merged_update)

        return None

    @staticmethod
    def _cta_label_patch(
        latest: str,
        next_ask: str | None,
        merged: CampaignData,
        skipped: set[str],
    ) -> _PreferencePatch | None:
        if next_ask != CTA_LABEL_FIELD:
            return None
        parsed = infer_cta_label_from_message(latest, campaign=merged) or parse_cta_label(latest)
        if parsed is None:
            return None
        return _PreferencePatch(
            {"cta": parsed},
            {},
            skipped | {CTA_LABEL_FIELD},
            merged.apply_updates({"cta": parsed}),
        )

    @staticmethod
    def _declining_tweaks_patch(
        latest: str,
        next_ask: str | None,
        skipped: set[str],
        merged: CampaignData,
        state: CampaignState,
        current_email_length: object,
        current_wants_follow_up: object,
    ) -> _PreferencePatch | None:
        if next_ask is not None or not is_declining_tweaks_message(latest):
            return None
        new_skipped = mark_all_optional_skipped(skipped)
        messages = state.get("messages")
        inferred_cta = infer_wants_cta_from_campaign(
            merged,
            messages if isinstance(messages, list) else None,
            wants_cta=state.get("wants_cta"),
        )
        prefs, delay, skip = fill_missing_preference_defaults(
            email_length=current_email_length,
            wants_follow_up=current_wants_follow_up,
            wants_cta=inferred_cta,
            follow_up_delay=state.get("follow_up_delay"),
            delegate=True,
        )
        if inferred_cta is not None:
            prefs["wants_cta"] = inferred_cta
        return _PreferencePatch(dict(prefs), dict(delay), new_skipped | skip)

    @staticmethod
    def _skip_field_patch(
        latest: str,
        next_ask: str | None,
        skipped: set[str],
        merged: CampaignData,
    ) -> _PreferencePatch | None:
        if not next_ask or not (is_skip_message(latest) or is_no_cta_message(latest)):
            return None
        if next_ask in (WANTS_CTA_FIELD, CTA_LABEL_FIELD, CTA_URL_FIELD):
            if has_cta_content(merged):
                return None
            return _PreferencePatch(
                {"wants_cta": False},
                {},
                skipped | {WANTS_CTA_FIELD, CTA_LABEL_FIELD, CTA_URL_FIELD},
                merged.apply_updates({"cta": None, "landing_page": None}),
            )
        new_skipped, patches = resolve_skip_for_field(
            next_ask,
            skipped,
            latest_message=latest,
        )
        merged_update = merged.apply_updates(patches)
        if next_ask == CTA_LABEL_FIELD and not patches:
            merged_update = merged.apply_updates({"cta": None})
        return _PreferencePatch({}, {}, new_skipped, merged_update)

    @staticmethod
    def _proceed_message_patch(
        latest: str,
        skipped: set[str],
        state: CampaignState,
        current_email_length: object,
        current_wants_follow_up: object,
    ) -> _PreferencePatch | None:
        if not is_proceed_message(latest):
            return None
        new_skipped = mark_all_optional_skipped(skipped)
        prefs, delay, skip = fill_missing_preference_defaults(
            email_length=current_email_length,
            wants_follow_up=current_wants_follow_up,
            wants_cta=state.get("wants_cta"),
            follow_up_delay=state.get("follow_up_delay"),
            delegate=True,
        )
        return _PreferencePatch(dict(prefs), dict(delay), new_skipped | skip)

    @staticmethod
    def _skip_or_proceed_patch(
        latest: str,
        next_ask: str | None,
        skipped: set[str],
        merged: CampaignData,
        state: CampaignState,
        current_email_length: object,
        current_wants_follow_up: object,
    ) -> _PreferencePatch | None:
        return (
            CampaignCollectionAgent._declining_tweaks_patch(
                latest,
                next_ask,
                skipped,
                merged,
                state,
                current_email_length,
                current_wants_follow_up,
            )
            or CampaignCollectionAgent._skip_field_patch(latest, next_ask, skipped, merged)
            or CampaignCollectionAgent._proceed_message_patch(
                latest,
                skipped,
                state,
                current_email_length,
                current_wants_follow_up,
            )
        )

    @staticmethod
    def _apply_next_ask_handlers(
        latest: str,
        next_ask: str | None,
        merged: CampaignData,
        skipped: set[str],
        state: CampaignState,
        current_email_length: object,
        current_wants_follow_up: object,
    ) -> tuple[dict[str, object], dict[str, object], set[str], CampaignData]:
        updates_prefs: dict[str, object] = {}
        updates_delay: dict[str, object] = {}
        patch = (
            CampaignCollectionAgent._preference_default_patch(
                next_ask,
                latest,
            )
            or CampaignCollectionAgent._wants_cta_patch(
                latest,
                next_ask,
                merged,
                skipped,
            )
            or CampaignCollectionAgent._cta_label_patch(
                latest,
                next_ask,
                merged,
                skipped,
            )
            or CampaignCollectionAgent._skip_or_proceed_patch(
                latest,
                next_ask,
                skipped,
                merged,
                state,
                current_email_length,
                current_wants_follow_up,
            )
        )
        if patch is not None:
            merged, skipped = _merge_preference_patches(
                updates_prefs,
                updates_delay,
                skipped,
                patch,
                merged,
            )
        return updates_prefs, updates_delay, skipped, merged

    @staticmethod
    def _apply_brief_follow_up_edits(
        latest: str,
        state: CampaignState,
        brief_editable: bool,
        updates_prefs: dict[str, object],
        updates_delay: dict[str, object],
        skipped: set[str],
    ) -> None:
        if not brief_editable:
            return
        if wants_to_enable_follow_up(latest):
            resolved_delay = resolve_follow_up_delay_for_edit(latest, state)
            updates_prefs["wants_follow_up"] = True
            updates_delay["follow_up_delay"] = resolved_delay.to_api_dict()
        elif wants_to_disable_follow_up(latest):
            updates_prefs["wants_follow_up"] = False
            updates_prefs["follow_up_delay"] = None
            updates_delay["follow_up_delay"] = None
        else:
            return
        skipped.discard(WANTS_FOLLOW_UP_FIELD)
        skipped.discard(FOLLOW_UP_DELAY_FIELD)

    @staticmethod
    def _should_apply_email_length(
        next_ask: str | None,
        brief_editable: bool,
        current_email_length: object,
        latest: str,
    ) -> bool:
        if next_ask == EMAIL_LENGTH_FIELD or brief_editable:
            return True
        return not has_email_length(current_email_length) and _is_short_preference_answer(latest)

    @staticmethod
    def _should_apply_wants_follow_up(
        next_ask: str | None,
        brief_editable: bool,
        current_wants_follow_up: object,
        latest: str,
    ) -> bool:
        if next_ask == WANTS_FOLLOW_UP_FIELD or brief_editable:
            return True
        return not has_wants_follow_up(current_wants_follow_up) and _is_short_preference_answer(
            latest,
        )

    @staticmethod
    def _apply_parsed_preference_messages(
        latest: str,
        next_ask: str | None,
        brief_editable: bool,
        state: CampaignState,
        messages: list[dict[str, str]],
        current_email_length: object,
        current_wants_follow_up: object,
        updates_prefs: dict[str, object],
        updates_delay: dict[str, object],
        skipped: set[str],
    ) -> None:
        parsed_length = parse_email_length_detail(latest)
        if parsed_length is not None and CampaignCollectionAgent._should_apply_email_length(
            next_ask,
            brief_editable,
            current_email_length,
            latest,
        ):
            updates_prefs["email_length"] = parsed_length.category
            if parsed_length.words is not None:
                updates_prefs["email_length_words"] = parsed_length.words
            skipped.discard(EMAIL_LENGTH_FIELD)

        parsed_wants_follow_up = parse_wants_follow_up(latest)
        if parsed_wants_follow_up is not None and CampaignCollectionAgent._should_apply_wants_follow_up(
            next_ask,
            brief_editable,
            current_wants_follow_up,
            latest,
        ):
            updates_prefs["wants_follow_up"] = parsed_wants_follow_up
            if not parsed_wants_follow_up:
                updates_prefs["follow_up_delay"] = None
            else:
                bundled_delay = parse_follow_up_delay(latest)
                if bundled_delay is not None:
                    updates_delay["follow_up_delay"] = bundled_delay.to_api_dict()
                    skipped.discard(FOLLOW_UP_DELAY_FIELD)
            skipped.discard(WANTS_FOLLOW_UP_FIELD)

        parsed_delay = parse_follow_up_delay(latest)
        if parsed_delay is not None and (
            next_ask == FOLLOW_UP_DELAY_FIELD
            or brief_editable
            or (
                parsed_wants_follow_up is True
                and "follow_up_delay" not in updates_delay
            )
        ):
            updates_delay["follow_up_delay"] = parsed_delay.to_api_dict()
            skipped.discard(FOLLOW_UP_DELAY_FIELD)
            return

        if next_ask == FOLLOW_UP_DELAY_FIELD and (
            is_affirmation_message(latest) or is_proceed_message(latest)
        ):
            resolved_delay = (
                follow_up_delay_from_state(state.get("follow_up_delay"))
                or infer_follow_up_delay_from_messages(messages)
                or DEFAULT_FOLLOW_UP_DELAY
            )
            updates_delay["follow_up_delay"] = resolved_delay.to_api_dict()
            skipped.add(FOLLOW_UP_DELAY_FIELD)

    @staticmethod
    def _unskip_fields_from_rule_extraction(
        messages: list[dict[str, str]],
        before: CampaignData,
        revision: bool,
        skipped: set[str],
    ) -> None:
        rule_updates = extract_from_latest_user_message(messages, before, revision=revision)
        for field in CampaignData.model_fields:
            before_val = getattr(before, field)
            after_val = getattr(rule_updates, field)
            if after_val and str(after_val).strip() and after_val != before_val:
                skipped.discard(field)

    @staticmethod
    def _should_reset_stale_artifacts(
        before: CampaignData,
        merged: CampaignData,
        revision: bool,
        latest: str,
        state: CampaignState,
    ) -> bool:
        if not campaign_changed(before, merged):
            return False
        if is_brief_approval_message(latest):
            return False
        if state.get("brief_status") in ("pending_approval", "approved"):
            return False
        return bool(revision or is_material_change(before, merged) or state.get("brief_approved"))

    async def _extract_merged_campaign(
        self,
        messages: list[dict[str, str]],
        before: CampaignData,
        revision: bool,
        state: CampaignState,
        latest: str,
    ) -> CampaignData:
        current = extract_from_latest_user_message(messages, before, revision=revision)
        extracted = await self._get_llm().extract_campaign_data(messages, current, revision=revision)
        merged = current.merge(extracted, revision=revision)
        merged = extract_from_latest_user_message(messages, merged, revision=revision)
        return self._normalize_merged_product_info(merged, state, latest)

    async def _apply_collection_preferences(
        self,
        state: CampaignState,
        merged: CampaignData,
        skipped: set[str],
        latest: str,
        messages: list[dict[str, str]],
        editing_brief: bool,
    ) -> tuple[CampaignData, set[str], dict[str, object], dict[str, object]]:
        current_wants_follow_up = state.get("wants_follow_up")
        current_wants_cta = state.get("wants_cta")
        current_email_length = state.get("email_length")
        next_ask = next_field_to_collect(
            merged,
            skipped,
            include_optional=editing_brief,
            follow_up_delay=state.get("follow_up_delay"),
            wants_follow_up=current_wants_follow_up,
            wants_cta=current_wants_cta,
            email_length=current_email_length,
            messages=messages,
        )
        updates_prefs, updates_delay, skipped, merged = self._apply_next_ask_handlers(
            latest,
            next_ask,
            merged,
            skipped,
            state,
            current_email_length,
            current_wants_follow_up,
        )
        merged = apply_field_defaults(
            merged,
            skipped,
            wants_cta=updates_prefs.get("wants_cta", current_wants_cta),
        )

        auto_name = await self._maybe_auto_name_campaign(state, merged)
        if auto_name:
            merged = merged.apply_updates({"campaign_name": auto_name})
            skipped.add("campaign_name")

        brief_editable = state.get("brief_status") in ("editing", "pending_approval")
        self._apply_brief_follow_up_edits(
            latest,
            state,
            brief_editable,
            updates_prefs,
            updates_delay,
            skipped,
        )
        self._apply_parsed_preference_messages(
            latest,
            next_ask,
            brief_editable,
            state,
            messages,
            current_email_length,
            current_wants_follow_up,
            updates_prefs,
            updates_delay,
            skipped,
        )
        return merged, skipped, updates_prefs, updates_delay

    async def _finalize_extraction_updates(
        self,
        state: CampaignState,
        before: CampaignData,
        merged: CampaignData,
        revision: bool,
        latest: str,
        messages: list[dict[str, str]],
        skipped: set[str],
        updates_prefs: dict[str, object],
        updates_delay: dict[str, object],
    ) -> dict[str, object]:
        inferred_wants_cta = infer_wants_cta_from_campaign(
            merged,
            messages,
            wants_cta=updates_prefs.get("wants_cta", state.get("wants_cta")),
        )
        if inferred_wants_cta is not None and updates_prefs.get("wants_cta") is not False:
            updates_prefs["wants_cta"] = inferred_wants_cta
            if inferred_wants_cta is True:
                skipped.add(WANTS_CTA_FIELD)

        updates: dict[str, object] = dict(apply_campaign_data(state, merged))
        updates.update(updates_prefs)
        updates.update(updates_delay)
        self._unskip_fields_from_rule_extraction(messages, before, revision, skipped)
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

        if self._should_reset_stale_artifacts(before, merged, revision, latest, state):
            updates.update(
                stale_artifact_reset(clear_brief=revision or is_material_change(before, merged)),
            )

        if not state.get("brief_approved") and "workflow" not in updates:
            updates["workflow"] = None

        draft_state: CampaignState = {**state, **updates}  # type: ignore[misc]
        updates["missing_fields"] = compute_collection_missing_fields(draft_state)
        return updates

    async def extract_and_update(self, state: CampaignState) -> dict[str, object]:
        """Analyze latest message, merge extractions, apply skip/delegate, return state patches."""
        messages = list(state.get("messages") or [])
        latest = self._latest_user_message(messages)

        if is_brief_approval_message(latest) and state.get("brief_status") in (
            "pending_approval",
            "approved",
        ):
            return self._approval_state_patch(state)

        before = campaign_data_from_state(state)
        revision = should_overwrite_campaign_fields(
            latest,
            brief_status=state.get("brief_status"),
        )
        skipped = normalize_skipped_fields(state.get("skipped_fields"))
        editing_brief = state.get("brief_status") == "editing"

        merged = await self._extract_merged_campaign(messages, before, revision, state, latest)
        merged, skipped, updates_prefs, updates_delay = await self._apply_collection_preferences(
            state,
            merged,
            skipped,
            latest,
            messages,
            editing_brief,
        )
        return await self._finalize_extraction_updates(
            state,
            before,
            merged,
            revision,
            latest,
            messages,
            skipped,
            updates_prefs,
            updates_delay,
        )

    def missing_fields_snapshot(self, state: CampaignState) -> dict[str, object]:
        return {"missing_fields": compute_collection_missing_fields(state)}

    async def build_next_question(
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

        if (
            is_skip_message(latest)
            and not is_brief_approval_message(latest)
            and not campaign.product_info
        ):
            return build_product_required_after_skip()

        context = build_collection_prompt_context(
            campaign,
            messages,
            editing_brief=editing_brief,
            skipped_fields=skipped,
            follow_up_delay=state.get("follow_up_delay"),
            wants_follow_up=state.get("wants_follow_up"),
            wants_cta=state.get("wants_cta"),
            email_length=state.get("email_length"),
            email_length_words=state.get("email_length_words"),
        )
        try:
            return await self._get_llm().generate(COLLECTION_REPLY_SYSTEM, context)
        except LLMProviderError:
            return build_collection_fallback_reply(
                campaign,
                editing_brief=editing_brief,
                skipped_fields=skipped,
                follow_up_delay=state.get("follow_up_delay"),
                wants_follow_up=state.get("wants_follow_up"),
                wants_cta=state.get("wants_cta"),
                email_length=state.get("email_length"),
                email_length_words=state.get("email_length_words"),
                messages=messages,
            )

    async def build_brief_reply(
        self,
        state: CampaignState,
        *,
        changes: list[str] | None = None,
    ) -> str:
        campaign = apply_field_defaults(
            campaign_data_from_state(state),
            normalize_skipped_fields(state.get("skipped_fields")),
        )
        messages = list(state.get("messages") or [])
        context = build_brief_reply_context(campaign, messages, changes=changes)
        system = BRIEF_UPDATE_REPLY_SYSTEM if changes else BRIEF_REPLY_SYSTEM
        try:
            return await self._get_llm().generate(system, context)
        except LLMProviderError:
            from app.services.conversation_response import (
                build_brief_approval_reply,
                build_brief_update_reply,
            )

            if changes:
                return build_brief_update_reply(changes)
            return build_brief_approval_reply(campaign)

    async def process_discovery_turn(self, state: CampaignState) -> CampaignCollectionTurnResult:
        """Full discovery turn: extract, refresh missing_fields, produce strategist reply."""
        updates = await self.extract_and_update(state)
        merged_state: CampaignState = {**state, **updates}  # type: ignore[misc]
        reply = await self.build_next_question(merged_state)
        updates["assistant_reply"] = reply
        return CampaignCollectionTurnResult(state_updates=updates, assistant_reply=reply)


campaign_collection_agent = CampaignCollectionAgent()
