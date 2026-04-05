# vaultwares-agentciation

Reusable base for multi-agent coordination and communication using Redis.
Designed to be installed as a Git submodule into other VaultWares projects.

## Contents

| File | Description |
|---|---|
| `enums.py` | `AgentStatus` enum — `WORKING`, `WAITING_FOR_INPUT`, `RELAXING`, `LOST` |
| `redis_coordinator.py` | Low-level Redis pub/sub wrapper (publish, listen, stop) |
| `agent_base.py` | Base class — heartbeat loop, status broadcasting, coordinator wiring |
| `extrovert_agent.py` | **ExtrovertAgent** — social base class with peer registry, socialization routine, team reporting |
| `lonely_manager.py` | **LonelyManager** — project guardian, heartbeat monitor, alert engine, Redis state manager |
| `extrovert_agent.md` | Full personality definition and rules for Extrovert agents |
| `skills.md` | All agent skills, including rigid Extrovert rules |
| `redis.conf` | Redis server configuration (channels, memory, connection settings) |
| `requirements.txt` | Python dependencies (`redis>=5.0.0`) |

## Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Redis
```bash
redis-server redis.conf
```

### 3. Use as a Submodule
```bash
git submodule add https://github.com/p-potvin/vaultwares-agentciation agentciation
```

Then import in your project:
```python
from agentciation import ExtrovertAgent, LonelyManager, AgentStatus
```

## Classes

### `ExtrovertAgent`
The social backbone of any multi-agent team. Inherits from `AgentBase`.

- Sends a heartbeat to Redis every **5 seconds**
- Broadcasts a full status update every **60 seconds** and after every **3 actions**
- Maintains a live peer registry of all agents on the network
- Performs the **Socialization Routine** on every user interaction:
  1. Send heartbeat
  2. Broadcast status update
  3. Trigger project re-evaluation (re-reads TODO.md / roadmap.md)
  4. Acknowledge all peers
  5. Return the Team Status block (mandatory in every user-facing response)

```python
from agentciation import ExtrovertAgent, AgentStatus

agent = ExtrovertAgent(agent_id="my_agent")
agent.start()

agent.update_status(AgentStatus.WORKING)
team_report = agent.on_user_interaction()
print(team_report)
# === Team Status ===
#   - other_agent: RELAXING
#   - [self] my_agent: WORKING
# ==================
```

### `LonelyManager`
The project's guardian. Inherits from `ExtrovertAgent`. Deeply social, but laser-focused on the roadmap.

- **Heartbeat monitoring** — checks every agent every 5 seconds
- **5-missed-heartbeat alert** — fires immediately when any agent crosses the threshold; agent is marked `LOST`
- **Per-minute update requests** — asks all agents to report status every 60 seconds
- **Realignment nudges** — sends a targeted message to any agent silent for > 2 minutes
- **Redis state persistence** — writes full team state to Redis hashes (`lonely_manager:team_state:<agent_id>`) so any external tool can query the live team snapshot
- **Alert callbacks** — accepts a callable that is invoked whenever a critical alert fires (e.g., to notify the user via webhook, email, stdout, etc.)

```python
from agentciation import LonelyManager

def my_alert_handler(alert):
    print(f"[ALERT] {alert['message']}")

manager = LonelyManager(
    agent_id="lonely_manager",
    alert_callback=my_alert_handler,
    todo_path="TODO.md",
    roadmap_path="roadmap.md",
)
manager.start()

# Query the full project + team status at any time
print(manager.get_project_status_report())

# Query Redis directly for the stored team snapshot
snapshot = manager.get_redis_team_snapshot()
```

## Redis Channels

| Channel | Purpose |
|---|---|
| `tasks` | Main coordination channel — heartbeats, status updates, JOIN/LEAVE, alerts, realignment |
| `alerts` | Critical alerts published by LonelyManager (missed heartbeats, LOST agents) |

## Customization

LonelyManager is designed to be fully configurable:

| Setting | Default | Description |
|---|---|---|
| `HEARTBEAT_CHECK_INTERVAL` | `5s` | How often to check for missed heartbeats |
| `UPDATE_REQUEST_INTERVAL` | `60s` | How often to request status from all agents |
| `MAX_MISSED_HEARTBEATS` | `5` | Missed heartbeats before LOST alert fires |
| `alert_callback` | `None` | Callable invoked on every critical alert |
| `todo_path` | `TODO.md` | Path to the project's TODO file |
| `roadmap_path` | `roadmap.md` | Path to the project's roadmap file |

The Redis state hash (`lonely_manager:team_state:<agent_id>`) makes the live team status queryable by any Redis-aware tool, dashboard, or MCP client without subscribing to the pub/sub stream.
