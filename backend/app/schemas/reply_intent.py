from enum import StrEnum


class ReplyIntent(StrEnum):
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    NEED_MORE_INFO = "need_more_info"
    BOOK_DEMO = "book_demo"


REPLY_INTENT_VALUES: frozenset[str] = frozenset(m.value for m in ReplyIntent)
