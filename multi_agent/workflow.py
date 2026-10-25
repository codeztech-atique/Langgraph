"""Wires the agents together into a LangGraph graph."""
from langgraph.graph import StateGraph, START, END

from .agents import (
    FINISH,
    AgentState,
    calculator,
    researcher,
    reviewer,
    route_from_supervisor,
    supervisor,
    writer,
)

WORKERS = {
    "researcher": researcher,
    "writer": writer,
    "reviewer": reviewer,
    "calculator": calculator,
}


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("supervisor", supervisor)
    for name, agent in WORKERS.items():
        builder.add_node(name, agent)
        # Every worker reports back to the supervisor when it's done.
        builder.add_edge(name, "supervisor")

    builder.add_edge(START, "supervisor")

    # The supervisor picks the next worker, or FINISH to end the run.
    # The mapping lists every possible destination so the graph can be drawn.
    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {**{name: name for name in WORKERS}, FINISH: END},
    )

    return builder.compile()


graph = build_graph()
