"""Lesson 5: Loops - a conditional edge that can point BACK to a node.

START -> guess --(wrong)--> guess ...
              \\--(right)--> END

This is the same pattern AI agents use: "think -> act -> check -> repeat".
"""
import random
from typing import Literal, TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    target: int
    guess: int
    attempts: int


def make_guess(state: State):
    guess = random.randint(1, 10)
    attempts = state.get("attempts", 0) + 1
    print(f"Attempt {attempts}: guessed {guess}")
    return {"guess": guess, "attempts": attempts}


def check(state: State) -> Literal["make_guess", "__end__"]:
    if state["guess"] == state["target"]:
        return END
    return "make_guess"


builder = StateGraph(State)
builder.add_node("make_guess", make_guess)
builder.add_edge(START, "make_guess")
builder.add_conditional_edges("make_guess", check)

graph = builder.compile()


if __name__ == "__main__":
    # recursion_limit caps the number of steps so a loop can't run forever.
    result = graph.invoke({"target": 7}, config={"recursion_limit": 50})
    print(f"\nFound {result['target']} in {result['attempts']} attempts")
