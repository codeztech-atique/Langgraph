"""
Lesson 07 - FinAdvise: a finance bot with LangGraph
Based on Edureka Module 4: "Demonstration: Building a Finance Bot with LangGraph"

No API keys or LLM needed - tools return mock data so we can focus on
state, nodes, conditional edges and memory.

Run:  python 07_finadvise_bot.py
"""
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------
# Step 1 - State: what the agent tracks during the conversation
# ---------------------------------------------------------------
class FinanceState(TypedDict):
    user_input: str   # raw text from the user
    intent: str       # stock | expense | budget | fallback
    data: str         # response from the tool (mocked)
    memory: dict      # context kept across interactions


# ---------------------------------------------------------------
# Step 2 - Nodes: each node does one job and returns state updates
# ---------------------------------------------------------------
def detect_intent(state: FinanceState):
    text = state["user_input"].lower()
    if "stock" in text or "price" in text:
        return {"intent": "stock"}
    if "spent" in text or "expense" in text or "add" in text:
        return {"intent": "expense"}
    if "budget" in text:
        return {"intent": "budget"}
    return {"intent": "fallback"}


def stock_info(state: FinanceState):
    # write to memory: remember what the user asked about
    memory = {**state.get("memory", {}), "last_stock_requested": state["user_input"]}
    return {"data": "AAPL is trading at $192.40 (mock data)", "memory": memory}


def track_expense(state: FinanceState):
    # read from memory: use what happened earlier in the conversation
    last = state.get("memory", {}).get("last_stock_requested", "nothing yet")
    return {"data": f"Expense added: '{state['user_input']}'. "
                    f"By the way, the last stock you checked was: {last}"}


def budget_summary(state: FinanceState):
    return {"data": "October: spent Rs 31,200 of Rs 40,000 budget (mock data)"}


def fallback(state: FinanceState):
    return {"data": "Sorry, I can help with stocks, expenses and budgets."}


# ---------------------------------------------------------------
# Step 3 - Graph: add nodes and connect them with edges
# ---------------------------------------------------------------
builder = StateGraph(FinanceState)
builder.add_node("Intent Detection", detect_intent)
builder.add_node("Stock Info", stock_info)
builder.add_node("Expense Tracker", track_expense)
builder.add_node("Budget Summary", budget_summary)
builder.add_node("Fallback", fallback)

builder.add_edge(START, "Intent Detection")
builder.add_conditional_edges(
    "Intent Detection",
    lambda state: state["intent"],          # intent decides the route
    {"stock": "Stock Info", "expense": "Expense Tracker",
     "budget": "Budget Summary", "fallback": "Fallback"},
)
for node in ["Stock Info", "Expense Tracker", "Budget Summary", "Fallback"]:
    builder.add_edge(node, END)

# ---------------------------------------------------------------
# Step 4 - Compile and run
# ---------------------------------------------------------------
graph = builder.compile()

if __name__ == "__main__":
    memory = {}
    for question in ["What is the AAPL stock price?",
                     "Add 500 for lunch",
                     "Show my budget",
                     "Tell me a joke"]:
        out = graph.invoke({"user_input": question, "memory": memory})
        memory = out["memory"]               # carry memory to the next turn
        print(f"You:  {question}\nBot:  [{out['intent']}] {out['data']}\n")

    # Uncomment to see the graph as Mermaid text:
    # print(graph.get_graph().draw_mermaid())
