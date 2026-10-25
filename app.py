"""Mock UI for the multi-agent graph in multi_agent/.

Run with:
    streamlit run app.py

What you'll see:
  - Left:  a chat, plus a live trace of every agent step as the graph streams.
  - Right: the graph with the running agent highlighted, and the shared state.
"""
import time

import streamlit as st

from multi_agent import AGENT_INFO, graph


EXAMPLES = [
    "What is LangGraph?",
    "Explain nodes, edges and state in LangGraph",
    "How does a supervisor work in a multi-agent system?",
    "Calculate (12 + 8) * 3",
    "Tell me about quantum physics",
]

ACTIVE_COLOR = "#ffd166"
VISITED_COLOR = "#bde0fe"
IDLE_COLOR = "#f2f0ff"


def graph_dot(active=None, visited=()):
    """Draw the compiled LangGraph as Graphviz DOT, colouring visited/active nodes."""
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
            f'"{node_id}" [label="{label}", shape={shape}, fillcolor="{color}", penwidth={penwidth}];'
        )
    for edge in drawable.edges:
        style = "dashed" if edge.conditional else "solid"
        lines.append(f'"{edge.source}" -> "{edge.target}" [style={style}];')
    lines.append("}")
    return "\n".join(lines)


def make_step(node, change):
    change = change or {}
    messages = change.get("messages", [])
    return {
        "node": node,
        "message": " ".join(entry["content"] for entry in messages),
        "update": {key: value for key, value in change.items() if key != "messages"},
    }


def render_step(step, number):
    icon = AGENT_INFO.get(step["node"], {}).get("icon", "")
    with st.container(border=True):
        st.markdown(f"**{number}.** {icon} **{step['node']}**: {step['message']}")
        # st.expander can't be nested, so use the collapsible JSON viewer instead.
        st.json(step["update"], expanded=False)


def render_run(run):
    with st.chat_message("user"):
        st.write(run["task"])
    with st.chat_message("assistant"):
        st.markdown(run["answer"])
        with st.expander(f"Agent trace ({len(run['steps'])} steps)"):
            for number, step in enumerate(run["steps"], start=1):
                render_step(step, number)


def run_graph(task, max_revisions, delay, graph_slot, state_slot):
    steps = []
    visited = {"__start__"}
    state = {}

    with st.status("Agents are working...", expanded=True) as status:
        # "updates" = what each node returned; "values" = full state after each step.
        for mode, chunk in graph.stream(
            {"task": task, "max_revisions": max_revisions},
            stream_mode=["updates", "values"],
        ):
            if mode == "updates":
                for node, change in chunk.items():
                    visited.add(node)
                    step = make_step(node, change)
                    steps.append(step)
                    status.update(label=f"{node} is working...")
                    graph_slot.graphviz_chart(graph_dot(active=node, visited=visited))
                    render_step(step, len(steps))
            else:
                state = chunk
                state_slot.json(state, expanded=True)
                if steps:
                    time.sleep(delay)

        status.update(label=f"Done in {len(steps)} steps", state="complete", expanded=False)

    visited.add("__end__")
    return {
        "task": task,
        "answer": state.get("final_answer", "(no answer)"),
        "steps": steps,
        "state": state,
        "visited": visited,
    }


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------

st.set_page_config(page_title="Multi-Agent Playground", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []
history = st.session_state.history

with st.sidebar:
    st.header("Settings")
    delay = st.slider(
        "Delay between steps (seconds)", 0.0, 2.0, 0.8, 0.1,
        help="Slows the run down so you can watch each agent work.",
    )
    max_revisions = st.slider(
        "Max writer revisions", 0, 3, 2,
        help="How many times the reviewer can send a draft back. Try 0 to skip revisions.",
    )
    if st.button("Clear chat"):
        history.clear()
        st.rerun()

    st.header("The agents")
    for name, info in AGENT_INFO.items():
        st.markdown(f"{info['icon']} **{name}**  \n{info['role']}")

    st.header("Legend")
    st.markdown(
        f"<span style='background:{ACTIVE_COLOR};padding:2px 6px;border-radius:4px'>running now</span> "
        f"<span style='background:{VISITED_COLOR};padding:2px 6px;border-radius:4px'>visited</span>  \n"
        "Solid arrow: fixed edge. Dashed arrow: conditional edge (the supervisor decides).",
        unsafe_allow_html=True,
    )

st.title("Multi-Agent Playground")
st.caption(
    "A mock UI for a LangGraph supervisor with four specialist agents. "
    "The agents are rule-based (no LLM, no API key), so you can focus on how work flows through the graph."
)

task = st.chat_input("Ask the agents something...")

chat_col, graph_col = st.columns([3, 2], gap="large")

with graph_col:
    st.subheader("Live graph")
    graph_slot = st.empty()
    st.subheader("Shared state")
    state_slot = st.empty()

last_run = history[-1] if history else None
graph_slot.graphviz_chart(graph_dot(visited=last_run["visited"] if last_run else ()))
state_slot.json(last_run["state"] if last_run else {}, expanded=False)

with chat_col:
    if not history and not task:
        st.info("Pick an example or type a question below to start.")

    example_cols = st.columns(3)
    for index, example in enumerate(EXAMPLES):
        if example_cols[index % 3].button(example, key=f"example-{example}"):
            task = example

    for run in history:
        render_run(run)

    if task:
        with st.chat_message("user"):
            st.write(task)
        with st.chat_message("assistant"):
            run = run_graph(task, max_revisions, delay, graph_slot, state_slot)
            st.markdown(run["answer"])
        history.append(run)
        graph_slot.graphviz_chart(graph_dot(visited=run["visited"]))
