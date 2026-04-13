from langgraph.graph import StateGraph, END
from core.state import AgentState
from agents.monitor_agent import monitor_agent
from agents.analysis_agent import analysis_agent
from agents.fix_agent import fix_agent
from agents.validation_agent import validation_agent
from agents.deploy_agent import deploy_agent

def should_retry_or_end(state: AgentState) -> str:
    if state["validation_passed"]:
        return "deploy"
    if state["retry_count"] >= 3:
        return "end"
    return "fix"

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("monitor", monitor_agent)
    graph.add_node("analysis", analysis_agent)
    graph.add_node("fix", fix_agent)
    graph.add_node("validation", validation_agent)
    graph.add_node("deploy", deploy_agent)

    graph.set_entry_point("monitor")
    graph.add_edge("monitor", "analysis")
    graph.add_edge("analysis", "fix")
    graph.add_edge("fix", "validation")

    graph.add_conditional_edges(
        "validation",
        should_retry_or_end,
        {
            "deploy": "deploy",
            "fix": "fix",
            "end": END,
        }
    )

    graph.add_edge("deploy", END)

    return graph.compile()

pipeline = build_graph()