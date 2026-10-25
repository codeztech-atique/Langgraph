"""Lesson 4: Conditional edges - let the state decide where to go next.

                 +--> positive --+
START -> classify|               |--> END
                 +--> negative --+
"""
from typing import Literal, TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    text: str
    mood: str
    reply: str


def classify(state: State):
    happy_words = {"good", "great", "love", "happy", "awesome"}
    words = set(state["text"].lower().split())
    return {"mood": "positive" if words & happy_words else "negative"}


def positive(state: State):
    return {"reply": "Glad to hear that!"}


def negative(state: State):
    return {"reply": "Sorry about that. How can I help?"}


# A router returns the NAME of the next node.
def route_by_mood(state: State) -> Literal["positive", "negative"]:
    return state["mood"]


builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_node("positive", positive)
builder.add_node("negative", negative)

builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route_by_mood)
builder.add_edge("positive", END)
builder.add_edge("negative", END)

graph = builder.compile()


if __name__ == "__main__":
    for text in ["I love LangGraph", "My code is broken"]:
        result = graph.invoke({"text": text})
        print(f"{text!r:25} -> {result['mood']:8} -> {result['reply']}")

    print("\nGraph diagram (paste into https://mermaid.live):")
    print(graph.get_graph().draw_mermaid())
