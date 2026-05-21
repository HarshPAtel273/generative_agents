# Generative Agents: Interactive Simulacra of Human Behavior

This repository contains the official code implementation for the research paper
[Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)
(Park et al., 2023, UIST '23), along with extensions for local LLM support,
performance optimizations, and simulation stability improvements.

<p align="center" width="100%">
<img src="cover.png" alt="Smallville" style="width: 80%; min-width: 300px; display: block; margin: auto;">
</p>

## What's New (This Fork)

Compared to the original paper implementation, this version adds:

- **Local LLM backend** — configurable via `openai_api_model` to use Ollama, vLLM, or any OpenAI-compatible server instead of the OpenAI API
- **One-hour-per-step simulation** — parallelized agent processing and animation fixes for running at 1 simulated hour per step
- **Simulation stability** — resume-in-place support, arena validation, and a `run-until` command for unattended runs
- **Optimized throughput** — removed blocking `time.sleep()` calls when using local inference servers

## System Architecture

```
generative_agents/
├── reverie/                    # Simulation backend (Python)
│   └── backend_server/
│       ├── reverie.py          # Main simulation loop
│       ├── utils.py            # LLM/embedding configuration
│       ├── maze.py             # Environment & pathfinding
│       └── persona/            # Agent cognitive architecture
│           ├── cognitive_modules/  # perceive, plan, reflect, converse, execute
│           ├── memory_structures/  # associative, spatial, scratch memory
│           └── prompt_template/    # LLM prompt wrappers
└── environment/                # Django frontend (visualization)
    └── frontend_server/
        ├── translator/         # Simulation state → web view
        ├── templates/          # Home (live) and demo (replay) views
        ├── storage/            # Saved simulation checkpoints
        └── static_dirs/        # Map tiles, character sprites
```

## Setup

### Prerequisites

- Python 3.9+
- A running LLM server (OpenAI API, or a local server via vLLM/Ollama)
- A running text-embedding server (or the OpenAI embeddings endpoint)

### Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r environment/frontend_server/requirements.txt
```

### Configure the LLM backend

Edit `reverie/backend_server/utils.py` to point at your inference server:

```python
# Example: OpenAI
openai_api_key = "sk-..."
openai_api_base = "https://api.openai.com/v1"
openai_api_model = "gpt-4o"
openai_api_embedding = "text-embedding-3-small"

# Example: local vLLM server
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8001/v1"
openai_api_model = "meta-llama/Llama-3-8B-Instruct"
openai_api_embedding = "nomic-ai/nomic-embed-text-v1.5"
```

Also set `maze_assets_loc` to point at the frontend static assets:

```python
maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
```

## Running a Simulation

### 1. Start the frontend server

```bash
cd environment/frontend_server
python manage.py runserver
```

The visualization will be available at `http://localhost:8000`.

### 2. Start the backend simulation

Open a second terminal and run:

```bash
cd reverie/backend_server
python reverie.py
```

When prompted:

```
Enter the name of the forked simulation: base_the_ville_isabella_maria_klaus
Enter the name of the new simulation: my_simulation
```

Use one of the provided base simulations (see [Base Simulations](#base-simulations)) or a previously saved checkpoint.

### 3. Step the simulation

Once the backend is running, enter commands at the prompt:

**Simulation control**

| Command | Description |
|---------|-------------|
| `run <number>` | Advance by that many steps (e.g. `run 100`) |
| `run until <step>` | Run until a specific step number (e.g. `run until 5000`) |
| `save` | Save current state without stopping |
| `fin` / `finish` / `f` | Save and exit |
| `exit` | Exit without saving (discards current run) |
| `start path tester mode` | Launch the path-tester tool (destructive — removes current sim folder) |

**Inspecting agent state** — replace `<Name>` with the full agent name (e.g. `Isabella Rodriguez`)

| Command | Description |
|---------|-------------|
| `print persona schedule <Name>` | Decomposed daily schedule for one agent |
| `print all persona schedule` | Decomposed daily schedule for all agents |
| `print hourly org persona schedule <Name>` | Original (non-decomposed) hourly schedule |
| `print persona current tile <Name>` | Current x/y tile coordinate |
| `print persona chatting with buffer <Name>` | Conversation cooldown buffer |
| `print persona associative memory (event) <Name>` | Long-term event memories |
| `print persona associative memory (thought) <Name>` | Long-term thought memories |
| `print persona associative memory (chat) <Name>` | Long-term chat memories |
| `print persona spatial memory <Name>` | Known locations tree |
| `print current time` | Current in-simulation time and step count |
| `print tile event <x>, <y>` | Events on a specific map tile |
| `print tile details <x>, <y>` | Full details of a specific map tile |

**Advanced**

| Command | Description |
|---------|-------------|
| `call -- analysis <Name>` | Open a stateless chat session with an agent (no memory written) |
| `call -- load history <csv_path>` | Inject whispered memories from a CSV file |

### Simulation step size

Each step represents 10 seconds by default. For faster runs you can configure the step to be one hour, which activates parallelized agent processing.

## Replaying a Simulation

To replay a saved simulation without running the backend:

1. Start the frontend server (`python manage.py runserver`).
2. Navigate to `http://localhost:8000/demo/<simulation_name>/<start_step>/<end_step>/`.

Example:

```
http://localhost:8000/demo/July1_the_ville_isabella_maria_klaus-step-3-20/0/100/
```

Included demo runs:

| Name | Steps |
|------|-------|
| `July1_the_ville_isabella_maria_klaus-step-3-5` | 3 agents, 5-step |
| `July1_the_ville_isabella_maria_klaus-step-3-11` | 3 agents, 11-step |
| `July1_the_ville_isabella_maria_klaus-step-3-20` | 3 agents, 20-step |

## Base Simulations

Base simulations are the starting states used to fork new runs.

| Name | Agents | Description |
|------|--------|-------------|
| `base_the_ville_isabella_maria_klaus` | 3 | Isabella, Maria, Klaus — default 3-agent world |
| `base_the_ville_n25` | 25 | 25-agent Smallville world |

Stored in `environment/frontend_server/storage/`.

## Compressing Simulation Storage

Saved simulations accumulate a large number of JSON files. To compress:

```bash
python reverie/compress_sim_storage.py <simulation_name>
```

Compressed archives are written to `environment/frontend_server/compressed_storage/`.

## Customizing Agents

Agent personas are defined in:

```
environment/frontend_server/storage/<simulation_name>/personas/<agent_name>/
├── bootstrap_memory/
│   ├── associative_memory/     # Long-term memories
│   ├── spatial_memory.json     # Known locations
│   └── scratch.json            # Working state (name, age, traits, goals)
```

Edit `scratch.json` to change an agent's name, age, personality traits, daily plan seed, and current action. After editing, fork a new simulation from that base.

## Agent Cognitive Architecture

Each agent runs a full perceive → retrieve → plan → execute → reflect loop every step:

1. **Perceive** (`perceive.py`) — observe nearby tiles, agents, and events
2. **Retrieve** (`retrieve.py`) — fetch relevant memories using embedding similarity
3. **Plan** (`plan.py`) — generate hourly or daily schedules via LLM
4. **Execute** (`execute.py`) — translate plans into map movements and actions
5. **Reflect** (`reflect.py`) — synthesize higher-level insights from recent memories
6. **Converse** (`converse.py`) — generate dialogue when agents meet

Prompts are versioned under `reverie/backend_server/persona/prompt_template/v3_ChatGPT/`.

## Requirements

Core Python packages (see `requirements.txt` for pinned versions):

- `openai>=1.14.0` — LLM and embedding API client
- `Django>=4.2,<5.0` — frontend web server
- `pandas`, `numpy` — data processing
- `nltk`, `gensim` — NLP utilities
- `scikit-learn` — memory retrieval scoring
- `aiohttp` — async HTTP for parallel LLM calls

## Citation

If you use this code in research, please cite the original paper:

```bibtex
@inproceedings{park2023generative,
  author = {Park, Joon Sung and O'Brien, Joseph C. and Cai, Carrie J. and
            Morris, Meredith Ringel and Liang, Percy and Bernstein, Michael S.},
  title = {Generative Agents: Interactive Simulacra of Human Behavior},
  booktitle = {Proceedings of the 36th Annual ACM Symposium on User Interface
               Software and Technology},
  series = {UIST '23},
  year = {2023},
  publisher = {ACM},
  doi = {10.1145/3586183.3606763},
}
```

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
