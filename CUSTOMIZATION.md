# Generative Agents — Customization Guide

This guide covers how to create new simulations, customize agents (personas), and modify the map. It assumes you have already completed the basic setup from `README.md`.

---

## Table of Contents

1. [Project Structure Overview](#1-project-structure-overview)
2. [Creating a New Simulation](#2-creating-a-new-simulation)
3. [Customizing Agents (Personas)](#3-customizing-agents-personas)
4. [Agent Memory: Seeding Initial Memories](#4-agent-memory-seeding-initial-memories)
5. [Configuring the LLM Backend](#5-configuring-the-llm-backend)
6. [Map Customization](#6-map-customization)
7. [Simulation Commands Reference](#7-simulation-commands-reference)
8. [Replaying and Demoing Simulations](#8-replaying-and-demoing-simulations)

---

## 1. Project Structure Overview

```
generative_agents/
├── reverie/
│   └── backend_server/
│       ├── reverie.py              ← simulation entry point
│       ├── utils.py                ← API keys, paths, model config
│       ├── maze.py                 ← world map loader
│       └── persona/
│           ├── persona.py          ← agent class
│           ├── memory_structures/  ← scratch, spatial, associative memory
│           └── cognitive_modules/  ← perceive, plan, reflect, execute, converse
└── environment/
    └── frontend_server/
        ├── storage/                ← all simulation save folders live here
        │   └── base_the_ville_isabella_maria_klaus/  ← starter simulation
        ├── compressed_storage/     ← compressed replays
        ├── temp_storage/           ← runtime handshake files
        └── static_dirs/assets/the_ville/
            └── matrix/             ← CSV tile maps
```

---

## 2. Creating a New Simulation

All simulations are **forked** from an existing one. The fork copies the entire save folder (agent memories, map state, positions) and gives it a new name.

### Step 1 — Choose a base simulation

| Base simulation | Agents | Notes |
|---|---|---|
| `base_the_ville_isabella_maria_klaus` | 3 | Lightweight, good for testing |
| `base_the_ville_n25` | 25 | Full town, heavier LLM load |

Both are in `environment/frontend_server/storage/`.

### Step 2 — Start the backend

```bash
cd reverie/backend_server
python reverie.py
```

You will be prompted:

```
Enter the name of the forked simulation: base_the_ville_isabella_maria_klaus
Enter the name of the new simulation: my-sim-name
```

- If `my-sim-name` **does not exist**, it is copied fresh from the fork source.
- If `my-sim-name` **already exists**, the simulation resumes from where it left off (no data is overwritten).

### Step 3 — Start the frontend

In a separate terminal:

```bash
cd environment/frontend_server
python manage.py runserver
```

Open `http://localhost:8000/simulator_home` in your browser.

### Simulation meta.json

Each simulation folder contains `reverie/meta.json` which you can edit **before** starting:

```json
{
  "fork_sim_code": "base_the_ville_isabella_maria_klaus",
  "start_date": "February 13, 2026",
  "curr_time": "February 13, 2026, 08:00:00",
  "sec_per_step": 10,
  "maze_name": "the_ville",
  "persona_names": [
    "Isabella Rodriguez",
    "Maria Lopez",
    "Klaus Mueller"
  ],
  "step": 0
}
```

| Field | Description |
|---|---|
| `fork_sim_code` | Source simulation this was copied from. Do not change after creation. |
| `start_date` | In-world calendar date the simulation begins. Format: `"Month DD, YYYY"` |
| `curr_time` | In-world current time. Automatically updated as simulation runs. |
| `sec_per_step` | How many in-world seconds each simulation step advances. Default `10`. Use `3600` for one-hour-per-step. |
| `maze_name` | Which map to load. Must match a folder under `static_dirs/assets/`. |
| `persona_names` | List of agent names. Each name must have a matching folder under `personas/`. |
| `step` | Current step counter. Set to `0` for a fresh start. |

### Adding or removing agents

Edit `persona_names` in `meta.json` and ensure a corresponding persona folder exists at:

```
storage/<sim_code>/personas/<Agent Name>/bootstrap_memory/
```

You can copy an existing persona folder and rename it, then edit the files inside (see Section 3).

---

## 3. Customizing Agents (Personas)

Each agent's identity and behavior is defined by three files inside `bootstrap_memory/`:

```
personas/<Agent Name>/bootstrap_memory/
├── scratch.json           ← personality, schedule, perception params
├── spatial_memory.json    ← which locations the agent knows about
└── associative_memory/
    ├── nodes.json         ← memory events, thoughts, and chats
    ├── embeddings.json    ← vector embeddings for each memory
    └── kw_strength.json   ← keyword frequency index
```

### scratch.json — Identity and Behavior

This is the most important file to edit when creating a new agent.

```json
{
  "name": "Isabella Rodriguez",
  "first_name": "Isabella",
  "last_name": "Rodriguez",
  "age": 34,

  "innate": "friendly, outgoing, hospitable",
  "learned": "Isabella Rodriguez is a cafe owner of Hobbs Cafe who loves to make people feel welcome.",
  "currently": "Isabella Rodriguez is planning a Valentine's Day party at Hobbs Cafe on February 14th at 5pm.",
  "lifestyle": "Isabella Rodriguez goes to bed around 11pm, wakes up around 6am.",
  "living_area": "the Ville:Isabella Rodriguez's apartment:main room",

  "daily_plan_req": "Isabella Rodriguez opens Hobbs Cafe at 8am everyday, and works at the counter until 8pm.",

  "vision_r": 8,
  "att_bandwidth": 8,
  "retention": 8,

  "daily_reflection_time": 180,
  "daily_reflection_size": 5,

  "recency_w": 1,
  "relevance_w": 1,
  "importance_w": 1,
  "recency_decay": 0.995
}
```

#### Identity fields

| Field | Description |
|---|---|
| `name` / `first_name` / `last_name` | Must match the folder name exactly. |
| `age` | Agent's age. Influences LLM-generated behavior. |
| `innate` | Core personality traits, comma-separated adjectives. These never change during the simulation. |
| `learned` | Background description: occupation, relationships, history. |
| `currently` | What the agent is currently focused on or working toward. Can be changed to redirect behavior mid-fork. |
| `lifestyle` | Daily rhythm (sleep/wake schedule). Used by the planner. |
| `living_area` | Home location in `World:Sector:Arena` format. Agent will return here to sleep. |
| `daily_plan_req` | High-level instruction given to the LLM each day to generate the agent's schedule. The main lever for controlling what an agent does each day. |

#### Perception parameters

| Field | Range | Description |
|---|---|---|
| `vision_r` | 1–16 | Tile radius of what the agent can see each step. Higher = more aware, more expensive. |
| `att_bandwidth` | 1–16 | Max number of perceived events the agent considers at once. |
| `retention` | 1–16 | How many recent events are kept in working memory. |

#### Memory and reflection parameters

| Field | Description |
|---|---|
| `daily_reflection_time` | In-world minute of day when the agent reflects (e.g., `180` = 3:00 AM). |
| `daily_reflection_size` | Number of high-level thoughts generated per reflection cycle. |
| `recency_w` | Weight of how recent a memory is when scoring relevance. |
| `relevance_w` | Weight of semantic similarity when scoring relevance. |
| `importance_w` | Weight of the LLM-rated importance score. |
| `recency_decay` | Exponential decay factor for recency. `0.995` ≈ slow decay. Lower = memories fade faster. |

### spatial_memory.json — Known Locations

Defines the hierarchical map of locations the agent knows. Format:

```json
{
  "the Ville": {
    "Isabella Rodriguez's apartment": {
      "main room": ["bed", "closet", "desk"],
      "bathroom": ["toilet", "sink", "shower"]
    },
    "Hobbs Cafe": {
      "cafe": ["coffee machine", "counter", "sofa"]
    }
  }
}
```

The structure is `World → Sector → Arena → [objects]`. Agents can only navigate to locations that appear in their spatial memory. If you add a new location to the map, add it here too for agents that should be able to go there.

---

## 4. Agent Memory: Seeding Initial Memories

You can inject backstory and memories into an agent before the simulation starts using a **history CSV file**.

### Create the CSV file

Place a CSV file anywhere under `static_dirs/assets/the_ville/` with the format:

```
Isabella Rodriguez,<statement 1>;<statement 2>;<statement 3>
Maria Lopez,<statement 1>;<statement 2>
```

Each row is one agent. Statements are separated by semicolons. Example:

```
Isabella Rodriguez,went to UC Berkeley;has been running Hobbs Cafe for five years;is best friends with Maria Lopez
Maria Lopez,studied culinary arts in college;moved to the Ville two years ago
```

### Load the history during a simulation run

While the simulation is running (at the `Enter option: ` prompt):

```
call -- load history the_ville/my_agent_history.csv
```

This injects the statements as memories into the named agents. Run this early (e.g., at step 1) before the agents start planning their day.

### Directly editing associative memory

For full control, you can manually edit `associative_memory/nodes.json`. Each node is a memory event:

```json
{
  "node_id": "001",
  "node_count": 1,
  "type_count": 1,
  "type": "event",
  "depth": 0,
  "created": "February 13, 2026, 08:00:00",
  "expiration": null,
  "subject": "Isabella Rodriguez",
  "predicate": "is",
  "object": "awake",
  "description": "Isabella Rodriguez is awake",
  "embedding_key": "Isabella Rodriguez is awake",
  "poignancy": 1,
  "keywords": ["Isabella Rodriguez"],
  "filling": []
}
```

Note: if you add nodes manually you must also add matching entries in `embeddings.json` (the vector embedding for the description string) and `kw_strength.json`. This is complex — using the CSV loader above is recommended.

---

## 5. Configuring the LLM Backend

Edit `reverie/backend_server/utils.py`:

```python
# OpenAI-compatible API key
openai_api_key = "your-key-here"

# API endpoint — use OpenAI's, a local Ollama, or a vLLM server
openai_api_url = "https://api.openai.com/v1"          # OpenAI
# openai_api_url = "http://localhost:11434/v1"         # Ollama (local)
# openai_api_url = "http://your-server:8001/v1"        # vLLM

# Model for agent reasoning
openai_api_model = "gpt-4o-mini"
# openai_api_model = "llama3.1:8b"                     # local Ollama model

# Embedding model (can be a separate server)
openai_api_embedding_model = "text-embedding-3-small"
openai_api_embedding_url = "https://api.openai.com/v1"
openai_api_embedding_key = "your-key-here"
```

> **Tip:** The reasoning model and embedding model can point to different servers. Running embeddings locally (e.g., `nomic-embed-text` via Ollama) while using a cloud model for reasoning is a common cost-saving configuration.

### sec_per_step and model speed

If your model is slow, increase `sec_per_step` in `meta.json` (e.g., `3600` for one hour per step). This reduces the total number of LLM calls needed to simulate a full day from ~8640 steps (at 10 sec/step) to 24 steps.

---

## 6. Map Customization

The map is defined as a set of CSV files in:

```
environment/frontend_server/static_dirs/assets/the_ville/matrix/
```

### maze_meta_info.json

```json
{
  "world_name": "the ville",
  "maze_width": 140,
  "maze_height": 100,
  "sq_tile_size": 32,
  "special_constraint": ""
}
```

This defines the grid dimensions. The visual tile size is 32×32 pixels.

### The five maze CSVs

Each CSV is a grid of integers (`maze_width` columns × `maze_height` rows). Each cell holds a numeric ID that maps to a name via the corresponding `special_blocks/` CSV.

| File | What it defines |
|---|---|
| `collision_maze.csv` | `32125` = blocked tile, `0` = walkable |
| `sector_maze.csv` | High-level area (e.g., "Isabella Rodriguez's apartment") |
| `arena_maze.csv` | Room within a sector (e.g., "main room") |
| `game_object_maze.csv` | Interactable object on the tile (e.g., "bed") |
| `spawning_location_maze.csv` | Named spawn points agents can be assigned to |

### special_blocks/ lookup CSVs

These map integer IDs to human-readable names. Format: `ID,Name`

```
# sector_blocks.csv
32138,the Ville:Isabella Rodriguez's apartment
32140,the Ville:Hobbs Cafe
```

The sector hierarchy uses colons: `World:Sector`. Arena and game object names are standalone strings.

### Editing the map

1. Use **Tiled Map Editor** (free, at [mapeditor.org](https://www.mapeditor.org)) to visually edit the map. The visual layer JSON files are at `static_dirs/assets/the_ville/the_ville_dec31.json` / `the_ville_jan7.json`.
2. After editing visuals, export/regenerate the corresponding maze CSV layers.
3. Update `special_blocks/` CSVs if you add new named areas.
4. Update agent `spatial_memory.json` so agents know about any new locations.

> **Important:** The `living_area` in `scratch.json` and all location references in `spatial_memory.json` must match the exact strings defined in your `special_blocks/` CSVs.

---

## 7. Simulation Commands Reference

While the simulation is running, type commands at the `Enter option: ` prompt:

| Command | Description |
|---|---|
| `run <N>` | Advance the simulation by N steps |
| `run until <step>` | Run until the simulation reaches a specific step number |
| `save` | Save all persona memory and simulation state to disk |
| `fin` | Save and exit cleanly |
| `exit` | Exit without saving |
| `call -- load history the_ville/<file>.csv` | Inject agent memories from a CSV file |

### What counts as a "step"

One step = one tile of movement per agent. At `sec_per_step = 10`, a full simulated day (24h) = **8,640 steps**. At `sec_per_step = 3600`, a full day = **24 steps**.

The simulation auto-saves on `fin`. Use `save` periodically during long runs.

---

## 8. Replaying and Demoing Simulations

Once a simulation has run, you can replay it in the browser without re-running the backend.

### Live replay

```
http://localhost:8000/replay/<sim_code>/<starting_step>/
```

Example: `http://localhost:8000/replay/my-sim-name/0/`

### Demo (compressed) replay

Compressed demos load faster and support speed control:

```
http://localhost:8000/demo/<sim_code>/<starting_step>/<speed>/
```

- `speed`: integer 1–5 (1 = slowest, 5 = fastest)
- Compressed simulations must be in `compressed_storage/`

### Compressing a simulation for demo

Copy your simulation folder from `storage/` to `compressed_storage/` and compress the movement and environment JSON files. See the existing entries in `compressed_storage/` as a reference for the expected format.

---

## Quick Reference: Common Tasks

| Task | What to edit |
|---|---|
| Change agent personality | `scratch.json` → `innate`, `learned`, `currently` |
| Change what agent does each day | `scratch.json` → `daily_plan_req` |
| Change agent home location | `scratch.json` → `living_area` |
| Add initial memories/backstory | Load a history CSV with `call -- load history ...` |
| Add a new agent | Add name to `meta.json`, create persona folder, copy and edit `scratch.json` |
| Remove an agent | Remove name from `meta.json` `persona_names` list |
| Change simulation speed (time per step) | `meta.json` → `sec_per_step` |
| Change simulation start date | `meta.json` → `start_date` and `curr_time` |
| Point to a different LLM | `utils.py` → `openai_api_url`, `openai_api_model` |
| Tune memory retrieval weights | `scratch.json` → `recency_w`, `relevance_w`, `importance_w` |
| Tune how far agents can see | `scratch.json` → `vision_r` |
