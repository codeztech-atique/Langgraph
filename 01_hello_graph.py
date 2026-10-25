"""Lesson 1: The smallest possible graph.

START -> step_one -> END
"""
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# 1. Define the State (the data passed between steps)
class State(TypedDict):
    messages: list[str]


# 2. Define a Node (a function that does the work)
#    A node receives the current state and returns a PARTIAL update.
def my_first_node(state: State):
    print("Node is running! Current state:", state)
    return {"messages": ["Hello from LangGraph!"]}


# 3. Build the Graph
builder = StateGraph(State)
builder.add_node("step_one", my_first_node)

# 4. Define the flow (Start -> step_one -> End)
builder.add_edge(START, "step_one")
builder.add_edge("step_one", END)

# 5. Compile the graph
graph = builder.compile()


if __name__ == "__main__":
    initial_state = {"messages": []}
    result = graph.invoke(initial_state)

    print("\nFinal Output:")
    print(result)
