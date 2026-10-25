"""Lesson 3: Reducers - APPEND to state instead of overwriting.

Annotated[list[str], operator.add] tells LangGraph how to merge a node's
update into the existing value: old_list + new_list.
"""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    messages: Annotated[list[str], operator.add]


def node_a(state: State):
    return {"messages": ["A was here"]}


def node_b(state: State):
    return {"messages": ["B was here"]}


def node_c(state: State):
    return {"messages": [f"C saw {len(state['messages'])} messages"]}


builder = StateGraph(State)
builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_node("c", node_c)

builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("b", "c")
builder.add_edge("c", END)

graph = builder.compile()


if __name__ == "__main__":
    result = graph.invoke({"messages": ["user started"]})
    for m in result["messages"]:
        print("-", m)
