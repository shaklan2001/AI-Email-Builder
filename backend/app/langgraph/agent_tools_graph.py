from langgraph.graph import END, StateGraph

from app.langgraph.agent_tools_nodes import execute_tool_node, select_tool_node
from app.langgraph.agent_tools_state import AgentToolsState

_compiled_agent_tools_graph = None


def build_agent_tools_graph():
    graph = StateGraph(AgentToolsState)
    graph.add_node("select_tool", select_tool_node)
    graph.add_node("execute_tool", execute_tool_node)
    graph.set_entry_point("select_tool")
    graph.add_edge("select_tool", "execute_tool")
    graph.add_edge("execute_tool", END)
    return graph.compile()


def get_agent_tools_graph():
    global _compiled_agent_tools_graph
    if _compiled_agent_tools_graph is None:
        _compiled_agent_tools_graph = build_agent_tools_graph()
    return _compiled_agent_tools_graph
