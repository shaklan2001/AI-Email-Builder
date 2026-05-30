from langgraph.graph import END, StateGraph

from app.langgraph.reply_nodes import classify_reply_intent_node
from app.langgraph.reply_state import ReplyHandlingState

_compiled_reply_graph = None


def build_reply_handling_graph():
    graph = StateGraph(ReplyHandlingState)
    graph.add_node("classify_intent", classify_reply_intent_node)
    graph.set_entry_point("classify_intent")
    graph.add_edge("classify_intent", END)
    return graph.compile()


def get_reply_handling_graph():
    global _compiled_reply_graph
    if _compiled_reply_graph is None:
        _compiled_reply_graph = build_reply_handling_graph()
    return _compiled_reply_graph
