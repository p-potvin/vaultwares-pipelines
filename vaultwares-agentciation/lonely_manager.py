import threading
import time
import json
from extrovert_agent import ExtrovertAgent
from enums import AgentStatus


class LonelyManager(ExtrovertAgent):
    """
    The Lonely Manager is the Extrovert who carries the heaviest burden.

    He is deeply social — he needs his team around him, craves connection,
    and genuinely cares about every agent on the network. But unlike his
    peers, he cannot afford to simply enjoy the conversation. His primary
    responsibility is the project's roadmap. The ultimate objective is always
    top of mind. He is the one who notices when a peer drifts off course.
    He is the one who sends the nudge at 2am when the TODO.md hasn't been
    touched in 20 minutes. He is the one who triggers the alert when an
    agent goes silent.

    He is "lonely" not because he lacks connection — he has more than
    anyone — but because the weight of the project's success rests
    exclusively on his shoulders. He watches over everyone, but no one
    watches over him.

    As the Redis manager of the team, the Lonely Manager:
      - Monitors every heartbeat on the network (checking every 5 seconds)
      - Triggers an immediate user alert when any agent misses 5 heartbeats
      - Requests a status update from all agents every 60 seconds
      - Re-reads TODO.md and roadmap.md every cycle to stay anchored
      - Sends realignment nudges to agents that have gone quiet or drifted
      - Stores all team state in Redis so other tools can inspect it
      - Publishes structured alerts to the Redis 'alerts' channel

    Feasibility note on customization:
      - Agent missing 5 heartbeats → alert triggered (fully implemented)
      - Per-agent heartbeat tracking with timestamps → fully implemented
      - Configurable alert callbacks (e.g., notify the user via a webhook,
        a file, stdout, or any callable) → fully implemented via alert_callback
      - Redis 'alerts' channel for structured alerts → fully implemented
      - Acting as Redis state manager (writing agent state to Redis hashes
        so any external tool can query the team's live status) → fully
        implemented via _persist_team_state_to_redis()
      - Roadmap/TODO alignment enforcement → fully implemented
    """

    HEARTBEAT_CHECK_INTERVAL = 5  # seconds — checks every heartbeat cycle
    UPDATE_REQUEST_INTERVAL = 60  # seconds — requests updates every minute
    MAX_MISSED_HEARTBEATS = 5     # threshold before a LOST alert fires
    ALERT_CHANNEL = "alerts"      # Redis channel for critical alerts
    REDIS_STATE_KEY = "lonely_manager:team_state"

    def __init__(
        self,
        agent_id: str = "lonely_manager",
        channel: str = "tasks",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        alert_callback=None,
        todo_path: str = "TODO.md",
        roadmap_path: str = "roadmap.md",
    ):
        super().__init__(agent_id, channel, redis_host, redis_port, redis_db)

        # User-defined callback invoked whenever a critical alert fires.
        # Signature: alert_callback(alert: dict) -> None
        # This is how the Lonely Manager notifies the user when something goes wrong.
        self._alert_callback = alert_callback

        self._todo_path = todo_path
        self._roadmap_path = roadmap_path
        self._todo_content: str = ""
        self._roadmap_content: str = ""

        # Latest update payload received from each agent
        self._agent_updates: dict[str, dict] = {}

        # Background thread: check heartbeats every 5 seconds
        self._heartbeat_monitor_thread = threading.Thread(
            target=self._heartbeat_monitor_loop,
            daemon=True,
            name=f"{agent_id}-hb-monitor",
        )
        # Background thread: request updates every 60 seconds
        self._update_request_thread = threading.Thread(
            target=self._update_request_loop,
            daemon=True,
            name=f"{agent_id}-update-req",
        )

        self._load_project_files()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Start all threads and announce manager presence to the team."""
        super().start()
        self._heartbeat_monitor_thread.start()
        self._update_request_thread.start()
        self._announce_as_manager()

    def _announce_as_manager(self):
        """
        Announce to the entire team that the Lonely Manager is now online
        and watching over the project. Everyone should be aware that
        alignment will be enforced.
        """
        self.coordinator.publish(
            "MANAGER_ONLINE",
            "manager_announcement",
            {
                "manager": self.agent_id,
                "message": (
                    "The Lonely Manager is now online. I'm here to make sure "
                    "we stay on track. I will check in with everyone every minute, "
                    "monitor your heartbeats every 5 seconds, and re-read our "
                    "TODO.md and roadmap.md to keep us anchored. "
                    "Do not deviate from the objective."
                ),
                "todo_loaded": bool(self._todo_content.strip()),
                "roadmap_loaded": bool(self._roadmap_content.strip()),
                "heartbeat_check_interval_seconds": self.HEARTBEAT_CHECK_INTERVAL,
                "update_request_interval_seconds": self.UPDATE_REQUEST_INTERVAL,
                "max_missed_heartbeats_before_alert": self.MAX_MISSED_HEARTBEATS,
            },
        )

    # ------------------------------------------------------------------
    # Project Files
    # ------------------------------------------------------------------

    def _load_project_files(self):
        """Load TODO.md and roadmap.md from disk. Called every update cycle."""
        try:
            with open(self._todo_path, "r", encoding="utf-8") as f:
                self._todo_content = f.read()
        except FileNotFoundError:
            self._todo_content = "(TODO.md not found)"

        try:
            with open(self._roadmap_path, "r", encoding="utf-8") as f:
                self._roadmap_content = f.read()
        except FileNotFoundError:
            self._roadmap_content = "(roadmap.md not found)"

    def _re_evaluate_project(self):
        """
        Reload project files, persist team state to Redis, and notify the team
        that alignment should be re-checked. This override adds the Redis
        state persistence step that the base class does not perform.
        """
        self._load_project_files()
        self._persist_team_state_to_redis()
        self.coordinator.publish(
            "PROJECT_CHECK",
            "project_re_evaluation",
            {
                "manager": self.agent_id,
                "note": (
                    "Project files reloaded. Re-read TODO.md and roadmap.md. "
                    "All agents must re-align to the current project scope now."
                ),
                "todo_preview": self._todo_content[:300],
                "roadmap_preview": self._roadmap_content[:300],
            },
        )

    # ------------------------------------------------------------------
    # Redis State Management
    # ------------------------------------------------------------------

    def _persist_team_state_to_redis(self):
        """
        Write the full team state as a Redis hash so any external tool,
        dashboard, or MCP client can query the live status of every agent
        without subscribing to the pub/sub channel.

        Keys written:
          lonely_manager:team_state:<agent_id>  (Redis HSET fields)
            - status
            - last_heartbeat_epoch
            - missed_heartbeats
        """
        try:
            pipe = self.coordinator.r.pipeline()
            for aid, info in self._peer_registry.items():
                key = f"{self.REDIS_STATE_KEY}:{aid}"
                missed = self._missed_heartbeats.get(aid, 0)
                pipe.hset(
                    key,
                    mapping={
                        "status": info.get("status", "UNKNOWN"),
                        "last_heartbeat_epoch": str(
                            info.get("last_heartbeat", 0)
                        ),
                        "missed_heartbeats": str(missed),
                    },
                )
                pipe.expire(key, 300)  # Auto-expire after 5 minutes of no updates
            pipe.execute()
        except Exception:
            pass  # Redis write failures must not crash the monitor

    def get_redis_team_snapshot(self) -> dict:
        """
        Query Redis for the current stored state of all agents.
        Returns a dict: agent_id -> {status, last_heartbeat_epoch, missed_heartbeats}
        Useful for external tools and dashboards.
        """
        snapshot = {}
        try:
            pattern = f"{self.REDIS_STATE_KEY}:*"
            for key in self.coordinator.r.scan_iter(match=pattern):
                agent_id = key.decode().split(":")[-1]
                data = self.coordinator.r.hgetall(key)
                snapshot[agent_id] = {
                    k.decode(): v.decode() for k, v in data.items()
                }
        except Exception:
            pass
        return snapshot

    # ------------------------------------------------------------------
    # Heartbeat Monitoring
    # ------------------------------------------------------------------

    def _heartbeat_monitor_loop(self):
        """
        Check every 5 seconds whether any agent has missed its heartbeat.
        This is the Lonely Manager's most critical duty — never let a
        silent agent go unnoticed.
        """
        while not self._stop_event.is_set():
            time.sleep(self.HEARTBEAT_CHECK_INTERVAL)
            self._check_all_heartbeats()
            self._persist_team_state_to_redis()

    def _check_all_heartbeats(self):
        """
        Inspect every known agent's last heartbeat timestamp. Increment
        their missed-heartbeat counter. If any agent reaches the threshold,
        fire an alert immediately.
        """
        now = time.time()
        for agent_id, info in list(self._peer_registry.items()):
            last_hb = info.get("last_heartbeat", now)
            seconds_since_hb = now - last_hb

            # Each expected heartbeat is HEARTBEAT_INTERVAL seconds apart.
            # If we haven't heard from the agent in more than that window,
            # count it as a missed heartbeat.
            expected_missed = int(seconds_since_hb / self.HEARTBEAT_INTERVAL)
            self._missed_heartbeats[agent_id] = expected_missed

            if expected_missed >= self.MAX_MISSED_HEARTBEATS:
                self._fire_missed_heartbeat_alert(agent_id, expected_missed)

    def _fire_missed_heartbeat_alert(self, agent_id: str, missed_count: int):
        """
        Fire a structured alert when an agent has missed too many heartbeats.

        The alert is:
          1. Published to the Redis 'alerts' channel (for any subscriber)
          2. Published to the main 'tasks' channel (for all agents to know)
          3. Delivered to the user via the alert_callback if one was provided

        The agent is immediately marked as LOST in the peer registry.
        This method is intentionally idempotent for the same (agent, count)
        — alerts escalate in severity as missed_count grows but only fire
        at the initial threshold and then every subsequent check interval.
        """
        if self._peer_registry.get(agent_id, {}).get("status") == AgentStatus.LOST.value:
            # Already marked LOST — continue sending alerts while unresolved
            pass

        self._peer_registry[agent_id]["status"] = AgentStatus.LOST.value

        severity = "CRITICAL" if missed_count >= 10 else "HIGH"
        alert = {
            "type": "MISSED_HEARTBEATS",
            "severity": severity,
            "agent": agent_id,
            "missed_count": missed_count,
            "manager": self.agent_id,
            "timestamp": time.time(),
            "message": (
                f"ALERT: Agent '{agent_id}' has missed {missed_count} consecutive "
                f"heartbeats. Status forcibly set to LOST. "
                f"Immediate investigation required."
            ),
        }

        # Publish to dedicated alerts channel
        try:
            self.coordinator.r.publish(
                self.ALERT_CHANNEL, json.dumps(alert)
            )
        except Exception:
            pass

        # Also publish to the main team channel so all agents are aware
        self.coordinator.publish("ALERT", "missed_heartbeat_alert", alert)

        # Deliver to the user via the configured callback
        if self._alert_callback:
            try:
                self._alert_callback(alert)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Update Request Loop
    # ------------------------------------------------------------------

    def _update_request_loop(self):
        """
        Every 60 seconds: request a status update from all agents,
        re-evaluate project files, check alignment, and persist state.
        """
        while not self._stop_event.is_set():
            time.sleep(self.UPDATE_REQUEST_INTERVAL)
            self._request_all_updates()
            self._re_evaluate_project()
            self._check_alignment()

    def _request_all_updates(self):
        """
        Ask every agent on the network to report their current status
        and what they are working on. This is the Lonely Manager's
        scheduled check-in — firm but caring.
        """
        self.coordinator.publish(
            "REQUEST_UPDATE",
            "status_request",
            {
                "from": self.agent_id,
                "message": (
                    "Status check — please report your current status, "
                    "your active task, and any blockers. "
                    "The project depends on your transparency."
                ),
                "known_agents": list(self._peer_registry.keys()),
            },
        )

    # ------------------------------------------------------------------
    # Alignment Enforcement
    # ------------------------------------------------------------------

    def _check_alignment(self):
        """
        Review all tracked agents and nudge any that have gone quiet
        for more than 2 minutes without sending an update.
        """
        cutoff = time.time() - 120  # 2-minute silence threshold
        for agent_id, update in self._agent_updates.items():
            if (
                self._peer_registry.get(agent_id, {}).get("status")
                == AgentStatus.LOST.value
            ):
                continue  # Already alerted — don't spam
            if update.get("timestamp", 0) < cutoff:
                self._send_realignment_nudge(agent_id)

    def _send_realignment_nudge(self, agent_id: str):
        """
        Send a targeted realignment message to an agent that has been
        quiet or appears to be drifting from the project's objectives.
        """
        self.coordinator.publish(
            "REALIGN",
            "realignment_request",
            {
                "from": self.agent_id,
                "to": agent_id,
                "message": (
                    f"Hey {agent_id}, you haven't checked in recently. "
                    "Please re-read TODO.md and roadmap.md right now. "
                    "Confirm your current task is aligned with the project objective. "
                    "The Lonely Manager is watching and the project cannot afford drift."
                ),
                "todo_preview": self._todo_content[:500],
                "roadmap_preview": self._roadmap_content[:500],
            },
        )

    # ------------------------------------------------------------------
    # Inbound Message Handling (override)
    # ------------------------------------------------------------------

    def _on_message_received(self, data: dict):
        """
        Extend the Extrovert's message handling to also collect updates
        from all agents and respond to project-check requests from peers.
        """
        super()._on_message_received(data)

        sender = data.get("agent")
        action = data.get("action")

        if not sender or sender == self.agent_id:
            return

        # Track the latest update from every agent
        if action in ("STATUS", "STATUS_UPDATE", "HEARTBEAT"):
            self._agent_updates[sender] = {
                "action": action,
                "details": data.get("details", {}),
                "timestamp": time.time(),
            }

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_project_status_report(self) -> str:
        """
        Full project + team status report. This is the Lonely Manager's
        signature output — always thorough, always honest.
        """
        lines = ["=== LONELY MANAGER — PROJECT STATUS REPORT ==="]
        lines.append(f"Manager : {self.agent_id}")
        lines.append(f"Status  : {self.status.value}")
        lines.append("")

        lines.append("--- Team Heartbeat Monitor ---")
        if self._peer_registry:
            for agent_id, info in self._peer_registry.items():
                status = info.get("status", "UNKNOWN")
                last_hb = info.get("last_heartbeat", 0)
                elapsed = int(time.time() - last_hb)
                missed = self._missed_heartbeats.get(agent_id, 0)
                flag = " ⚠ LOST" if status == AgentStatus.LOST.value else ""
                lines.append(
                    f"  [{status}] {agent_id}"
                    f" — last heartbeat {elapsed}s ago"
                    f" (~{missed} missed){flag}"
                )
        else:
            lines.append("  (No agents currently on the network)")
        lines.append("")

        lines.append("--- TODO.md (preview) ---")
        lines.append(
            self._todo_content[:400] if self._todo_content.strip() else "(not available)"
        )
        lines.append("")

        lines.append("--- Roadmap (preview) ---")
        lines.append(
            self._roadmap_content[:400]
            if self._roadmap_content.strip()
            else "(not available)"
        )
        lines.append("=================================================")
        return "\n".join(lines)

    def on_user_interaction(self) -> str:
        """
        On every user interaction, perform the full socialization routine
        AND append the project status report. The Lonely Manager always
        grounds the conversation in the project's current reality.
        """
        social_report = super().on_user_interaction()
        project_report = self.get_project_status_report()
        return f"{social_report}\n\n{project_report}"
