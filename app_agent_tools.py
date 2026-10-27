"""Streamlit UI for lesson 06_agent_tools.py.

Watch the ReAct loop live:
  START -> agent --(needs a tool)--> tools --+
             ^                               |
             +------- (loop back) -----------+
           agent --(has the answer)--> END

Run with:
    .venv/bin/streamlit run app_agent_tools.py
"""
import importlib.util
import sys
import time
from pathlib import Path

import streamlit as st

# Load 06_agent_tools.py even though the filename starts with a number.
# Register it in sys.modules first so TypedDict type hints resolve.
_MODULE_PATH = Path(__file__).with_name("06_agent_tools.py")
_spec = importlib.util.spec_from_file_location("agent_tools_lesson", _MODULE_PATH)
_lesson = importlib.util.module_from_spec(_spec)
sys.modules["agent_tools_lesson"] = _lesson
_spec.loader.exec_module(_lesson)

graph = _lesson.graph
TOOLS = _lesson.TOOLS

EXAMPLES = [
    "What is the TSLA stock price?",
    "What is the AAPL stock price?",
    "I spent 500 on lunch",
    "How is my budget?",
    "Tell me a joke",
]

ACTIVE_COLOR = "#ffd166"
VISITED_COLOR = "#bde0fe"
IDLE_COLOR = "#f2f0ff"

NODE_HELP = {
    "agent": (
        "REASON step. The agent reads the state and either "
        "picks a tool (`tool_call`) or writes the final `answer`."
    ),
    "tools": (
        "ACT + OBSERVE step. Runs the chosen tool from TOOLS and "
        "writes the result into `observation`, then clears `tool_call`."
    ),
}


def graph_dot(active=None, visited=()):
    drawable = graph.get_graph()
    lines = [
        "digraph {",
        'rankdir=TB; bgcolor="transparent";',
        'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12];',
        'edge [color="#888888", arrowsize=0.7];',
    ]
    for node_id in drawable.nodes:
        label = {"__start__": "START", "__end__": "END"}.get(node_id, node_id)
        shape = "ellipse" if node_id in ("__start__", "__end__") else "box"
        if node_id == active:
            color = ACTIVE_COLOR
        elif node_id in visited:
            color = VISITED_COLOR
        else:
            color = IDLE_COLOR
        penwidth = 2.5 if node_id == active else 1
        lines.append(
            f'"{node_id}" [label="{label}", shape={shape}, '
            f'fillcolor="{color}", penwidth={penwidth}];'
        )
    for edge in drawable.edges:
        style = "dashed" if edge.conditional else "solid"
        lines.append(f'"{edge.source}" -> "{edge.target}" [style={style}];')
    lines.append("}")
    return "\n".join(lines)


def render_step(node, change, number):
    with st.container(border=True):
        st.markdown(f"**{number}.** Node: `{node}`")
        st.caption(NODE_HELP.get(node, ""))
        for thought in change.get("steps", []):
            st.markdown(f"- {thought}")
        update = {key: value for key, value in change.items() if key != "steps"}
        if update:
            st.json(update, expanded=True)


def run_graph(question, delay, graph_slot, state_slot):
    steps = []
    visited = {"__start__"}
    state = {}

    with st.status("Invoking the graph...", expanded=True) as status:
        # stream_mode:
        #   "updates" -> what THIS node returned (partial update)
        #   "values"  -> full state AFTER LangGraph merged that update
        for mode, chunk in graph.stream(
            {"question": question},
            stream_mode=["updates", "values"],
        ):
            if mode == "updates":
                for node, change in chunk.items():
                    visited.add(node)
                    steps.append({"node": node, "change": change or {}})
                    status.update(label=f"`{node}` is running...")
                    graph_slot.graphviz_chart(graph_dot(active=node, visited=visited))
                    render_step(node, change or {}, len(steps))
            else:
                state = chunk
                state_slot.json(state, expanded=True)
                if steps:
                    time.sleep(delay)

        status.update(
            label=f"Done in {len(steps)} node runs",
            state="complete",
            expanded=False,
        )

    visited.add("__end__")
    return {
        "question": question,
        "answer": state.get("answer", "(no answer)"),
        "steps": steps,
        "state": state,
        "visited": visited,
    }


def render_run(run):
    with st.chat_message("user"):
        st.write(run["question"])
    with st.chat_message("assistant"):
        st.markdown(run["answer"])
        with st.expander(f"Invocation trace ({len(run['steps'])} node runs)"):
            for number, step in enumerate(run["steps"], start=1):
                render_step(step["node"], step["change"], number)


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------

st.set_page_config(page_title="Agent + Tools Playground", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []
history = st.session_state.history

with st.sidebar:
    st.header("Settings")
    delay = st.slider(
        "Delay between steps (seconds)",
        0.0,
        2.0,
        0.8,
        0.1,
        help="Slows the run so you can watch each node.",
    )
    if st.button("Clear chat"):
        history.clear()
        st.rerun()

    st.header("How invoke works here")
    st.markdown(
        """
1. UI calls `graph.stream({"question": ...})`.
2. LangGraph starts at **agent**.
3. If agent sets `tool_call`, the conditional edge goes to **tools**.
4. **tools** runs the Python function, writes `observation`, clears `tool_call`.
5. Fixed edge sends control back to **agent**.
6. Agent sees `observation`, writes `answer`, and the router chooses END.
        """
    )

    st.header("Available tools")
    for name, fn in TOOLS.items():
        st.markdown(f"**`{name}`**  \n{fn.__doc__}")

    st.header("Legend")
    st.markdown(
        f"<span style='background:{ACTIVE_COLOR};padding:2px 6px;border-radius:4px'>running now</span> "
        f"<span style='background:{VISITED_COLOR};padding:2px 6px;border-radius:4px'>visited</span>  \n"
        "Solid arrow: fixed edge. Dashed arrow: conditional edge (`should_continue`).",
        unsafe_allow_html=True,
    )

st.title("Agent + Tools Playground")
st.caption(
    "UI for `06_agent_tools.py`. Rule-based ReAct loop — no API key. "
    "Ask a question and watch agent → tools → agent."
)

question = st.chat_input("Ask about stocks, expenses, or budget...")

chat_col, graph_col = st.columns([3, 2], gap="large")

with graph_col:
    st.subheader("Live graph")
    graph_slot = st.empty()
    st.subheader("Shared state after each step")
    state_slot = st.empty()

last_run = history[-1] if history else None
graph_slot.graphviz_chart(graph_dot(visited=last_run["visited"] if last_run else ()))
state_slot.json(last_run["state"] if last_run else {}, expanded=False)

with chat_col:
    if not history and not question:
        st.info("Pick an example or type a question to invoke the graph.")

    example_cols = st.columns(3)
    for index, example in enumerate(EXAMPLES):
        if example_cols[index % 3].button(example, key=f"example-{example}"):
            question = example

    for run in history:
        render_run(run)

    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            run = run_graph(question, delay, graph_slot, state_slot)
            st.markdown(run["answer"])
        history.append(run)
        graph_slot.graphviz_chart(graph_dot(visited=run["visited"]))
