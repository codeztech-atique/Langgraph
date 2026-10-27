"""Lesson 6: A simple agent that uses tools.

START -> agent --(needs a tool)--> tools --+
           ^                               |
           +------- (loop back) -----------+
         agent --(has the answer)--> END

This is the ReAct loop: Reason -> Act (call a tool) -> Observe -> repeat.
It combines every earlier lesson: state, nodes, a reducer, a conditional
edge and a loop.

The agent's "brain" is rule-based so it runs without an API key.
In a real app, an LLM reads the tool descriptions and decides which one to call.
"""
import operator
from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph import StateGraph, START, END


# 1. Tools: plain Python functions the agent is allowed to call
def get_stock_price(ticker: str) -> str:
    """Get the latest price for a stock ticker."""
    prices = {"AAPL": 192.40, "MSFT": 415.10, "TSLA": 248.50}  # mock data
    return f"{ticker} is trading at ${prices.get(ticker, 100.0)}"


def add_expense(amount: int, item: str) -> str:
    """Record an expense."""
    return f"Added expense: Rs {amount} for {item}"


def get_budget() -> str:
    """Show this month's budget summary."""
    return "October: Rs 31,200 spent of Rs 40,000 budget"


TOOLS = {
    "get_stock_price": get_stock_price,
    "add_expense": add_expense,
    "get_budget": get_budget,
}


# 2. State: what the agent carries through the loop
class State(TypedDict, total=False):
    question: str
    steps: Annotated[list[str], operator.add]  # reducer: every step is appended
    tool_call: Optional[dict]                  # the tool the agent wants to run
    observation: str                           # what the last tool returned
    answer: str


# 3. Agent node (REASON): call a tool, or give the final answer
def agent(state: State):
    if state.get("observation"):
        return {"answer": state["observation"],
                "steps": ["Thought: I have what I need, so I can answer."]}

    question = state["question"].lower().replace("?", "")
    words = question.split()

    if "stock" in question or "price" in question:
        ticker = next((w.upper() for w in words if w.upper() in ("AAPL", "MSFT", "TSLA")), "AAPL")
        call = {"name": "get_stock_price", "args": {"ticker": ticker}}
    elif "spent" in question or "add" in question:
        amount = next((int(w) for w in words if w.isdigit()), 0)
        call = {"name": "add_expense", "args": {"amount": amount, "item": words[-1]}}
    elif "budget" in question:
        call = {"name": "get_budget", "args": {}}
    else:
        return {"answer": "I can help with stock prices, expenses and budgets.",
                "steps": ["Thought: no tool fits, so I answer directly."]}

    return {"tool_call": call,
            "steps": [f"Thought: I should call {call['name']}({', '.join(map(repr, call['args'].values()))})"]}


# 4. Tool node (ACT + OBSERVE): run the chosen tool and save the result
def tools(state: State):
    call = state["tool_call"]
    result = TOOLS[call["name"]](**call["args"])
    return {"observation": result, "tool_call": None,
            "steps": [f"Action: {call['name']}  ->  Observation: {result}"]}


# 5. Router: go to the tools if the agent asked for one, otherwise finish
def should_continue(state: State) -> Literal["tools", "__end__"]:
    return "tools" if state.get("tool_call") else END


builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", tools)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue)
builder.add_edge("tools", "agent")  # loop back so the agent sees the result

graph = builder.compile()


if __name__ == "__main__":
    for question in ["What is the TSLA stock price?",
                     "I spent 500 on lunch",
                     "How is my budget?",
                     "Tell me a joke"]:
        result = graph.invoke({"question": question})
        print(f"\nYou:   {question}")
        for step in result["steps"]:
            print(f"       {step}")
        print(f"Agent: {result['answer']}")

    print("\nGraph diagram (paste into https://mermaid.live):")
    print(graph.get_graph().draw_mermaid())