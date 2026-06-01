from langgraph.graph import END, StateGraph

from app.langgraph.nodes import (
    campaign_brief_node,
    extract_information_node,
    generate_emails_node,
    generate_workflow_node,
    missing_information_node,
    question_generator_node,
    route_after_missing_information,
)
from app.langgraph.state import CampaignState

_compiled_graph = None


def build_campaign_graph():
    graph = StateGraph(CampaignState)
    graph.add_node("extract_information", extract_information_node)
    graph.add_node("missing_information", missing_information_node)
    graph.add_node("question_generator", question_generator_node)
    graph.add_node("campaign_brief", campaign_brief_node)
    graph.add_node("generate_workflow", generate_workflow_node)
    graph.add_node("generate_emails", generate_emails_node)
    graph.set_entry_point("extract_information")
    graph.add_edge("extract_information", "missing_information")
    graph.add_conditional_edges(
        "missing_information",
        route_after_missing_information,
        {
            "question_generator": "question_generator",
            "campaign_brief": "campaign_brief",
            "generate_workflow": "generate_workflow",
        },
    )
    graph.add_edge("question_generator", END)
    graph.add_edge("campaign_brief", END)
    graph.add_edge("generate_workflow", "generate_emails")
    graph.add_edge("generate_emails", END)
    return graph.compile()


def get_campaign_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_campaign_graph()
    return _compiled_graph
