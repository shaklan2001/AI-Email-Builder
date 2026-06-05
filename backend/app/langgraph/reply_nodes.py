from app.agents.reply_intent_agent import reply_intent_agent
from app.langgraph.reply_state import ReplyHandlingState
from app.repositories.lead_repository import lead_status_for_reply_intent
from app.schemas.reply_intent import ReplyIntent


async def classify_reply_intent_node(state: ReplyHandlingState) -> dict[str, str]:
    intent = await reply_intent_agent.classify(
        reply_body=str(state.get("reply_body") or ""),
        reply_subject=state.get("reply_subject"),
        product_context=state.get("product_context"),
    )
    lead_status = lead_status_for_reply_intent(intent)
    return {
        "reply_intent": intent.value,
        "lead_status": lead_status.value,
    }
