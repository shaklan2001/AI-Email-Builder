from enum import StrEnum


class ReplyIntent(StrEnum):
    INTERESTED = "interested"
    BOOK_DEMO = "book_demo"
    PRICING = "pricing"
    QUESTION = "question"
    NEEDS_INFO = "needs_info"
    NOT_INTERESTED = "not_interested"
    UNSUBSCRIBE = "unsubscribe"
    UNKNOWN = "unknown"


REPLY_INTENT_VALUES: frozenset[str] = frozenset(m.value for m in ReplyIntent)

# Legacy input aliases accepted from older clients / stored documents
REPLY_INTENT_ALIASES: dict[str, ReplyIntent] = {
    "need_more_info": ReplyIntent.NEEDS_INFO,
    "needs_info": ReplyIntent.NEEDS_INFO,
    "need_info": ReplyIntent.NEEDS_INFO,
    "more_info": ReplyIntent.NEEDS_INFO,
    "book_demo": ReplyIntent.BOOK_DEMO,
}
