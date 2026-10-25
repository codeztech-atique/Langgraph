# LangGraph Learning Project

A few small, self-contained lessons to learn how LangGraph works.
No API keys or LLMs are needed; every lesson uses plain Python functions.

## Requirements

- Python 3.9 or newer (3.11+ recommended)
- `langgraph`
- `streamlit` (only for the UI in `app.py`)

## Setup

Open a terminal and go to the project folder (the quotes matter because the path has spaces and `&`):

```bash
cd "/Users/atique1201gmail.com/Desktop/LangGraph & LangChain/Langgraph"
```

Install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

### Optional: use a virtual environment

A virtual environment keeps this project's packages separate from the rest of your system.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run `deactivate` when you're done. Next time, just run `source .venv/bin/activate` again before running the lessons.

## Running the lessons

Run each file with `python3`:

```bash
python3 01_hello_graph.py
python3 02_multiple_nodes.py
python3 03_reducers.py
python3 04_conditional_edges.py
python3 05_loops.py
python3 06_multi_agent.py
```

Lesson 6 also accepts your own question:

```bash
python3 06_multi_agent.py "Explain reducers and state in LangGraph"
```

Or run them all at once:

```bash
for f in 0*.py; do echo "===== $f ====="; python3 "$f"; done
```

In Cursor you can also open any lesson file and click the Run button in the top-right corner.

## The lessons

| File | Concept | Expected output |
|---|---|---|
| `01_hello_graph.py` | State, a node, edges, `compile()`, `invoke()` | `{'messages': ['Hello from LangGraph!']}` |
| `02_multiple_nodes.py` | Chaining nodes; updates overwrite by default; `stream()` | `HELLO, ATIQUE!!!` |
| `03_reducers.py` | Appending to a list with `Annotated[list, operator.add]` | Four messages, one per step |
| `04_conditional_edges.py` | A router function picks the next node | A positive and a negative reply, plus a Mermaid diagram |
| `05_loops.py` | A node that loops back to itself until a condition is met | Random guesses until it finds 7 |
| `06_multi_agent.py` | A supervisor agent delegating to specialist agents | A numbered trace of which agent did what, then the final answer |

For lesson 4, paste the printed diagram into [mermaid.live](https://mermaid.live) to see the graph drawn.

## Multi-agent system (lesson 6)

The code lives in the `multi_agent/` folder:

- `multi_agent/agents.py`: the shared state and each agent's logic
- `multi_agent/workflow.py`: how the agents are wired into a graph

It uses the **supervisor pattern**. The supervisor looks at the shared state, picks which specialist should work next, and every specialist reports back to the supervisor when it's done:

```
                 +--> researcher --+
                 +--> writer ------+
START -> supervisor --> reviewer ------+--> back to supervisor
                 +--> calculator --+
                 +--> END (when the job is done)
```

| Agent | Job |
|---|---|
| supervisor | Reads the state and decides who works next, or finishes |
| researcher | Looks up facts in a small built-in knowledge base |
| writer | Writes an answer from the research, and rewrites it when the reviewer asks |
| reviewer | Approves the draft, or rejects it and sends it back to the writer |
| calculator | Solves arithmetic such as `(12 + 8) * 3` |

The agents are rule-based stand-ins for LLMs, so everything runs without an API key. The writer's first draft is deliberately incomplete, so you can watch the reviewer reject it and send it back.

## Mock UI

`app.py` is a Streamlit app that lets you watch the multi-agent graph run. Start it with:

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501). Press `Ctrl+C` in the terminal to stop it.

What the UI shows:

- **Chat (left)**: type a question or click an example. Each agent step appears live, showing what the agent said and the exact state update it returned.
- **Live graph (right)**: the agent that's running now is yellow, and agents already used in this run are blue. Dashed arrows are conditional edges, where the supervisor decides.
- **Shared state (right)**: the full LangGraph state after each step.
- **Sidebar settings**: slow down or speed up the steps, and change how many times the reviewer can send a draft back (set it to 0 to see the loop skipped).

Things to try:

- "Explain nodes, edges and state in LangGraph": the full research, write, review and rewrite loop.
- "Calculate (12 + 8) * 3": the supervisor sends it straight to the calculator.
- "Tell me about quantum physics": the researcher finds nothing, and the writer handles it.
- Add your own facts to `KNOWLEDGE_BASE` in `multi_agent/agents.py`, then ask about them.

## Core ideas

- **State**: a `TypedDict` holding the data shared across the graph.
- **Node**: a function that receives the state and returns a dict with only the keys it wants to change.
- **Edge**: sets which node runs next. `START` and `END` mark the entry and exit.
- **Conditional edge**: a function that returns the name of the next node, chosen at runtime.
- **Reducer**: controls how a node's update is merged into the state (replace by default, or e.g. append).
- **`compile()`**: turns the builder into a runnable graph. `invoke()` returns the final state; `stream()` yields each step.

## Troubleshooting

- **`NotOpenSSLWarning` or `LangChainPendingDeprecationWarning`** is printed on every run. These are harmless and can be ignored.
- **`ModuleNotFoundError: No module named 'langgraph'`**: install it with `python3 -m pip install langgraph`. If you're using a virtual environment, make sure it's activated.
- **`GraphRecursionError`** in lesson 5: the loop hit `recursion_limit` before finding the number. Run it again or raise the limit.
- **`streamlit: command not found`**: activate the virtual environment first (`source .venv/bin/activate`), or run `python3 -m streamlit run app.py`.
- **Streamlit suggests installing `watchdog`**: optional. It only makes the app reload faster when you edit files.
- **Port 8501 is already in use**: another Streamlit app is running. Stop it, or run `streamlit run app.py --server.port 8502`.
