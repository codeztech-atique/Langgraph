"""The shared state and the agents (nodes) of the multi-agent graph.

Pattern: SUPERVISOR + WORKERS ("hub and spoke")

                 +--> researcher --+
                 +--> writer ------+
START -> supervisor --> reviewer ------+--> back to supervisor
                 +--> calculator --+
                 +--> END (when the job is done)

Every agent here is a plain Python function. In a real app, the body of each
function would call an LLM (and maybe tools). They are rule-based here so you
can run everything without an API key and get the same result every time.
"""
import ast
import operator
import re
from typing import Annotated, Optional, TypedDict


FINISH = "FINISH"


class LogEntry(TypedDict):
    agent: str
    content: str


class AgentState(TypedDict, total=False):
    # Input
    task: str
    max_revisions: int

    # Shared conversation log; the reducer APPENDS each agent's entries.
    messages: Annotated[list[LogEntry], operator.add]

    # Written by the supervisor
    next_agent: str
    final_answer: str

    # Written by the workers
    research: list[str]
    calc_result: str
    draft: str
    revisions: int
    review_status: str  # "pending" | "approved" | "rejected"
    feedback: str


AGENT_INFO = {
    "supervisor": {
        "icon": ":material/hub:",
        "role": "Reads the state and decides which agent works next, or finishes.",
    },
    "researcher": {
        "icon": ":material/search:",
        "role": "Looks up facts about the task in a small knowledge base.",
    },
    "writer": {
        "icon": ":material/edit_note:",
        "role": "Turns the research into an answer, and rewrites it on feedback.",
    },
    "reviewer": {
        "icon": ":material/rate_review:",
        "role": "Checks the draft covers all the research; approves or rejects it.",
    },
    "calculator": {
        "icon": ":material/calculate:",
        "role": "Solves arithmetic like (12 + 8) * 3.",
    },
}


def _log(agent: str, content: str) -> list[LogEntry]:
    return [{"agent": agent, "content": content}]


# --------------------------------------------------------------------------
# Supervisor
# --------------------------------------------------------------------------

def supervisor(state: AgentState):
    task = state["task"]
    max_revisions = state.get("max_revisions", 2)

    if extract_expression(task):
        if state.get("calc_result") is None:
            return _route("calculator", "This looks like math, sending it to the calculator.")
        return _finish(state["calc_result"], "Calculator has the result. Done!")

    if state.get("research") is None:
        return _route("researcher", "No research yet, asking the researcher to gather facts.")

    if not state.get("draft"):
        return _route("writer", "Research is ready, asking the writer for a first draft.")

    status = state.get("review_status")
    revisions = state.get("revisions", 0)

    if status == "pending":
        return _route("reviewer", "A new draft is ready, asking the reviewer to check it.")

    if status == "rejected" and revisions < max_revisions:
        return _route(
            "writer",
            f"Reviewer asked for changes, sending it back to the writer "
            f"(revision {revisions + 1} of {max_revisions}).",
        )

    if status == "rejected":
        return _finish(state["draft"], "Revision limit reached, delivering the latest draft.")

    return _finish(state["draft"], "Reviewer approved the draft. Done!")


def _route(agent: str, reason: str):
    return {"next_agent": agent, "messages": _log("supervisor", reason)}


def _finish(answer: str, reason: str):
    return {"next_agent": FINISH, "final_answer": answer, "messages": _log("supervisor", reason)}


def route_from_supervisor(state: AgentState) -> str:
    return state["next_agent"]


# --------------------------------------------------------------------------
# Researcher
# --------------------------------------------------------------------------

KNOWLEDGE_BASE = {
    "langgraph": "LangGraph is a library for building stateful, multi-step AI workflows as graphs of nodes and edges.",
    "node": "A node is a Python function that receives the current state and returns an update.",
    "edge": "An edge decides which node runs next; conditional edges pick the next node at runtime.",
    "state": "The state is shared data (usually a TypedDict) that every node can read and update.",
    "reducer": "A reducer controls how an update is merged into the state, for example appending to a list instead of replacing it.",
    "supervisor": "A supervisor is an agent that routes work to specialist agents and decides when the job is done.",
    "multi-agent": "A multi-agent system splits a job across several specialised agents that share one state.",
    "agent": "An agent is a node, usually backed by an LLM, that decides what to do next and may call tools.",
    "python": "Python is the most popular language for AI development, and LangGraph is written in it.",
}


def researcher(state: AgentState):
    text = state["task"].lower()
    facts = [fact for keyword, fact in KNOWLEDGE_BASE.items() if keyword in text]

    if facts:
        note = f"Found {len(facts)} relevant fact(s) in the knowledge base."
    else:
        note = "Found nothing about this topic in the knowledge base."
    return {"research": facts, "messages": _log("researcher", note)}


# --------------------------------------------------------------------------
# Writer
# --------------------------------------------------------------------------

def writer(state: AgentState):
    facts = state.get("research", [])
    revisions = state.get("revisions", 0)

    if not facts:
        draft = f"Sorry, I couldn't find anything about \"{state['task']}\" in my knowledge base."
        note = "No facts to work with, wrote a polite 'not found' answer."
    elif state.get("review_status") == "rejected":
        draft = " ".join(facts)
        revisions += 1
        note = f"Rewrote the draft based on feedback: {state.get('feedback', '')}"
    else:
        # Deliberately incomplete, so the reviewer has something to reject.
        draft = facts[0]
        note = "Wrote a quick first draft."

    return {
        "draft": draft,
        "revisions": revisions,
        "review_status": "pending",
        "messages": _log("writer", note),
    }


# --------------------------------------------------------------------------
# Reviewer
# --------------------------------------------------------------------------

def reviewer(state: AgentState):
    facts = state.get("research", [])
    missing = [fact for fact in facts if fact not in state["draft"]]

    if missing:
        feedback = f"The draft covers {len(facts) - len(missing)} of {len(facts)} facts. Add the missing ones."
        return {
            "review_status": "rejected",
            "feedback": feedback,
            "messages": _log("reviewer", f"Rejected. {feedback}"),
        }
    return {
        "review_status": "approved",
        "feedback": "",
        "messages": _log("reviewer", "Looks good. Approved."),
    }


# --------------------------------------------------------------------------
# Calculator
# --------------------------------------------------------------------------

_MATH_CHARS = re.compile(r"^[\d\s.+\-*/()%^]+$")
_MATH_PREFIXES = ("what is", "what's", "calculate", "compute", "solve")

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def extract_expression(task: str) -> Optional[str]:
    text = task.lower().strip().rstrip("?").strip()
    for prefix in _MATH_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    has_digit = any(ch.isdigit() for ch in text)
    has_operator = any(op in text for op in "+-*/%^")
    if text and _MATH_CHARS.match(text) and has_digit and has_operator:
        return text.replace("^", "**")
    return None


def safe_eval(expression: str) -> float:
    """Evaluate arithmetic without using eval()."""

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            left, right = _eval(node.left), _eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("exponent too large")
            return _OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](_eval(node.operand))
        raise ValueError("unsupported expression")

    return _eval(ast.parse(expression, mode="eval"))


def calculator(state: AgentState):
    expression = extract_expression(state["task"])
    try:
        value = safe_eval(expression)
        if isinstance(value, float):
            value = round(value, 6)
        result = f"{expression.replace('**', '^')} = {value}"
        note = f"Calculated {result}."
    except (ValueError, ZeroDivisionError, SyntaxError) as error:
        result = f"I couldn't calculate '{expression}': {error}."
        note = result
    return {"calc_result": result, "messages": _log("calculator", note)}
