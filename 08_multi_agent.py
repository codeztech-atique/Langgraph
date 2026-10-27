"""Lesson 6: Multi-agent - a supervisor that delegates to specialist agents.

The agents live in the multi_agent/ folder:
  - multi_agent/agents.py    the shared state + each agent's logic
  - multi_agent/workflow.py  how the agents are wired into a graph

Run with a default set of examples:
    python3 06_multi_agent.py

Or ask your own question:
    python3 06_multi_agent.py "Explain nodes and edges in LangGraph"
"""
import sys

from multi_agent import graph


EXAMPLES = [
    "Explain nodes, edges and state in LangGraph",
    "Calculate (12 + 8) * 3",
    "Tell me about quantum physics",
]


def run(task: str, max_revisions: int = 2):
    print(f"\n{'=' * 70}\nTASK: {task}\n{'=' * 70}")

    final_answer = None
    step = 0
    for update in graph.stream({"task": task, "max_revisions": max_revisions}):
        for node, change in update.items():
            step += 1
            for entry in change.get("messages", []):
                print(f"{step:>2}. [{entry['agent']:>10}] {entry['content']}")
            final_answer = change.get("final_answer", final_answer)

    print(f"\nFINAL ANSWER:\n{final_answer}")


if __name__ == "__main__":
    tasks = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else EXAMPLES
    for task in tasks:
        run(task)
