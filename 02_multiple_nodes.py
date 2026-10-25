"""Lesson 2: Chaining nodes, and why the default update OVERWRITES.

START -> greet -> shout -> END

Each node returns only the keys it wants to change. Without a reducer,
the returned value replaces the old value for that key.
"""
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    name: str
    greeting: str


def greet(state: State):
    return {"greeting": f"Hello, {state['name']}"}


def shout(state: State):
    # Reads what the previous node wrote, then overwrites it.
    return {"greeting": state["greeting"].upper() + "!!!"}


builder = StateGraph(State)
builder.add_node("greet", greet)
builder.add_node("shout", shout)

builder.add_edge(START, "greet")
builder.add_edge("greet", "shout")
builder.add_edge("shout", END)

graph = builder.compile()


if __name__ == "__main__":
    # stream() shows the update produced by each node as it runs.
    for update in graph.stream({"name": "Atique"}):
        print(update)

    print("\nFinal:", graph.invoke({"name": "Atique"}))
