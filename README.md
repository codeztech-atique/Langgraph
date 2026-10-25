# LangGraph Learning Project

Small lessons for learning LangGraph, plus a browser UI for the multi-agent graph.
No API keys or LLMs are needed. Every agent is a plain Python function.

## Requirements

- Python 3.9 or newer (3.11+ recommended)
- Packages in `requirements.txt`: `langgraph` and `streamlit`

## Setup

Open a terminal in this project folder, then run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

In Cursor, the project folder is already the terminal's starting directory, so you can paste those two commands as they are. From another terminal, `cd` into the cloned folder first. Put quotes around the path if it contains spaces or `&`.

`.venv` is local only. It is listed in `.gitignore` and is not on GitHub. After a fresh clone, create it again with the commands above.

Use the Python and Streamlit inside `.venv`. The system `python3` and a bare `streamlit` command do not see these packages.

## Run a lesson

```bash
.venv/bin/python 01_hello_graph.py
.venv/bin/python 02_multiple_nodes.py
.venv/bin/python 03_reducers.py
.venv/bin/python 04_conditional_edges.py
.venv/bin/python 05_loops.py
.venv/bin/python 06_multi_agent.py
```

Lesson 6 accepts your own question:

```bash
.venv/bin/python 06_multi_agent.py "Explain reducers and state in LangGraph"
```

## Run the UI

`app.py` is the browser UI. It does not run lessons 01–05. It runs the same graph as lesson 6, imported from `multi_agent/`:

- `multi_agent/agents.py` — supervisor, researcher, writer, reviewer, calculator
- `multi_agent/workflow.py` — how those agents are connected

Start it with the Streamlit binary inside the virtual environment:

```bash
.venv/bin/streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501). Press `Ctrl+C` in that terminal to stop it.

`streamlit run app.py` fails with `command not found: streamlit` until the virtual environment is on your `PATH`. `python3 app.py` also fails, because the system Python does not have Streamlit and Streamlit has to launch the file.

If you prefer to activate the environment first:

```bash
source .venv/bin/activate
streamlit run app.py
```

Your prompt should show `(.venv)` after `source`. Run `deactivate` when you are done.

### What you see

- **Chat (left):** type a question or click an example. Each agent step is numbered as it finishes.
- **Live graph (right):** the agent running now is yellow. Agents already used in this run are blue. Dashed arrows are conditional edges.
- **Shared state (right):** the LangGraph state after each step.
- **Sidebar:** slow the steps down, or set "Max writer revisions" to `0` to skip the rewrite loop.

The step numbers are not a fixed list of six. `app.py` numbers every node that finishes. The supervisor in `multi_agent/agents.py` chooses the next agent, and each worker returns to the supervisor. A normal question is about seven steps (supervisor, researcher, supervisor, writer, supervisor, reviewer, supervisor). A maths question is three steps (supervisor, calculator, supervisor). Several matching facts add a rewrite loop and the run grows past seven steps.

Things to try:

- "Explain nodes, edges and state in LangGraph" — research, write, review, and rewrite
- "Calculate (12 + 8) * 3" — goes straight to the calculator
- "Tell me about quantum physics" — the researcher finds nothing
- Add a fact to `KNOWLEDGE_BASE` in `multi_agent/agents.py`, then ask about it

## Lessons

| File | Concept | Expected output |
|---|---|---|
| `01_hello_graph.py` | State, a node, edges, `compile()`, `invoke()` | `{'messages': ['Hello from LangGraph!']}` |
| `02_multiple_nodes.py` | Chaining nodes; updates overwrite by default; `stream()` | `HELLO, ATIQUE!!!` |
| `03_reducers.py` | Appending to a list with `Annotated[list, operator.add]` | Four messages, one per step |
| `04_conditional_edges.py` | A router function picks the next node | A positive and a negative reply, plus a Mermaid diagram |
| `05_loops.py` | A node that loops back to itself until a condition is met | Random guesses until it finds 7 |
| `06_multi_agent.py` | Supervisor delegating to specialist agents | A numbered trace, then the final answer |
| `app.py` | The same graph as lesson 6, drawn in the browser | UI at http://localhost:8501 |

For lesson 4, paste the printed diagram into [mermaid.live](https://mermaid.live).

## How the multi-agent graph runs

```
                 +--> researcher --+
                 +--> writer ------+
START -> supervisor --> reviewer ------+--> back to supervisor
                 +--> calculator --+
                 +--> END
```

| Agent | Job |
|---|---|
| supervisor | Reads the state and decides who works next, or finishes |
| researcher | Looks up facts in the built-in knowledge base |
| writer | Writes an answer from the research, and rewrites it after a rejection |
| reviewer | Approves the draft, or rejects it and sends it back to the writer |
| calculator | Solves arithmetic such as `(12 + 8) * 3` |

The writer's first draft is incomplete on purpose when more than one fact matches, so you can see the reviewer send it back.

## Core ideas

- **State**: a `TypedDict` shared across the graph.
- **Node**: a function that receives the state and returns only the keys it changes.
- **Edge**: which node runs next. `START` and `END` are the entry and exit.
- **Conditional edge**: a function that returns the next node's name at runtime.
- **Reducer**: how an update is merged (replace by default, or append).
- **`compile()`**: turns the builder into a runnable graph. `invoke()` returns the final state. `stream()` yields each step.

## Troubleshooting

- **`zsh: command not found: streamlit`**: run `.venv/bin/streamlit run app.py`, or `source .venv/bin/activate` first.
- **`ModuleNotFoundError: No module named 'streamlit'`** or **`langgraph`**: you used system `python3`. Run `.venv/bin/python` or `.venv/bin/streamlit` instead. If `.venv` does not exist, repeat the Setup commands.
- **`NotOpenSSLWarning` or `LangChainPendingDeprecationWarning`**: harmless. Ignore them.
- **`GraphRecursionError`** in lesson 5: the loop hit `recursion_limit` before finding the number. Run it again.
- **Port 8501 is already in use**: the UI is already running. Open http://localhost:8501, or stop the other process and start again.
- **Streamlit suggests installing `watchdog`**: optional. It only reloads the app faster when you edit files.
