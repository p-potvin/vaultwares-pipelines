import os
import re
import sys
import json
import time
import threading
import logging
import redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s | [%(levelname)s] | %(message)s")
logger = logging.getLogger("Dispatcher")

# Add root for custom coordinator
sys.path.append(os.getcwd())

TASKS_FILE = os.path.join(os.getcwd(), "TASKS.md")

class DispatcherAgentLogic:
    def __init__(self, redis_host='localhost', redis_port=6379, db=0):
        self.agent_id = 'dispatcher-agent'
        # Standardize connection like ai_model/redis_coordination.py
        self.r = redis.Redis(host=redis_host, port=redis_port, db=db, decode_responses=True)
        self.pubsub = self.r.pubsub()
        # Listen for task events and agent statuses
        self.pubsub.subscribe('tasks')
        self.tasks = []
        self.agent_registry = {}
        self.running = True

    def parse_tasks(self):
        if not os.path.exists(TASKS_FILE):
            logger.error(f"{TASKS_FILE} not found.")
            return []
        
        parsed = []
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in lines:
            line_str = line.strip()
            # Main tasks: N [status] title
            main_match = re.match(r"^(\d+)\s+\[(.*?)\]\s+(.*)$", line_str)
            if main_match:
                parsed.append({
                    "id": main_match.group(1),
                    "status": main_match.group(2).strip(),
                    "title": main_match.group(3).strip(),
                    "type": "main"
                })
                continue
            
            # Sub tasks: N[a-z] [status] title
            sub_match = re.match(r"^(\d+[a-z]+)\s+\[(.*?)\]\s+(.*)$", line_str)
            if sub_match:
                parsed.append({
                    "id": sub_match.group(1),
                    "status": sub_match.group(2).strip(),
                    "title": sub_match.group(3).strip(),
                    "type": "subtask"
                })
        self.tasks = parsed
        return parsed

    def update_dashboard(self):
        "Clears console locally and prints live status of queue and agents."
        # Optional: Print raw dashboard to see current pending queue
        free_main = [t for t in self.tasks if t['status'] == ' ' and t['type'] == 'main']
        free_sub = [t for t in self.tasks if t['status'] == ' ' and t['type'] == 'subtask']
        print(f"\r\033[K[DASHBOARD] Queue: {len(free_main)} Main, {len(free_sub)} Subtasks | Online Agents: {len(self.agent_registry)}", end="")

    def listen_loop(self):
        "Background thread to process Redis messages and track agents"
        logger.info("Starting Redis communication listener...")
        for message in self.pubsub.listen():
            if not self.running:
                break
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    agent = data.get('agent', 'Unknown')
                    action = data.get('action', '')
                    target = data.get('target', None)
                    task_id = data.get('task', None)

                    # Watch status events locally
                    if action == 'STATUS':
                        status_val = data.get('details', {}).get('status', 'UNKNOWN')
                        
                        # Only log state changes to minimize noise
                        prev_state = self.agent_registry.get(agent, {}).get('status', 'UNKNOWN')
                        if prev_state != status_val:
                            logger.info(f"\n[STATE_CHANGE] {agent} transitioned from {prev_state} to {status_val}")
                            
                        self.agent_registry[agent] = {
                            "status": status_val,
                            "task": task_id,
                            "last_seen": time.time()
                        }
                    elif action in ('LOG', 'MSG', 'BLOCKED'):
                        msg_text = data.get('details', {}).get('message', '')
                        logger.info(f"\n[{action}] {agent}: {msg_text}")
                    elif action == 'COMPLETE':
                        logger.info(f"\n[COMPLETE] {agent} finished {task_id}")
                        self.agent_registry[agent] = {
                            "status": "RELAXING",
                            "task": None,
                            "last_seen": time.time()
                        }
                except json.JSONDecodeError:
                    pass

    def start_communications(self):
        t = threading.Thread(target=self.listen_loop, daemon=True)
        t.start()

    def dispatch_loop(self):
        "Continually match free agents with pending tasks."
        self.start_communications()
        logger.info("Dispatcher is active and looking for free agents in RELAXING state.")
        
        try:
            while self.running:
                self.parse_tasks()
                
                free_main = [t for t in self.tasks if t['type'] == 'main' and t['status'] == ' ']
                free_sub = [t for t in self.tasks if t['type'] == 'subtask' and t['status'] == ' ']
                
                # Check all known agents
                for agent_id, info in self.agent_registry.items():
                    if info.get('status', '').upper() == 'RELAXING':
                        # Default mock rule: Subtasks take priority, or assign sequentially
                        t_assigned = None
                        if free_sub:
                            t_assigned = free_sub.pop(0)
                        elif free_main:
                            t_assigned = free_main.pop(0)
                            
                        if t_assigned:
                            # Send assignment via Redis PubSub 'tasks' channel
                            assign_msg = {
                                "agent": self.agent_id,
                                "action": "ASSIGN",
                                "target": agent_id,
                                "task": t_assigned["id"],
                                "details": {"title": t_assigned["title"]}
                            }
                            self.r.publish("tasks", json.dumps(assign_msg))
                            logger.info(f"\n[DISPATCH] Assigned '{t_assigned['type']}' task {t_assigned['id']} to {agent_id}")
                            
                            # Locally update agent's state to prevent double assignment in same tick
                            self.agent_registry[agent_id]['status'] = 'WORKING'
                            self.agent_registry[agent_id]['task'] = t_assigned["id"]

                self.update_dashboard()
                time.sleep(2)  # Check internal heartbeat
                
        except KeyboardInterrupt:
            self.running = False
            logger.info("\nShutting down Dispatcher...")

if __name__ == "__main__":
    dispatcher_core = DispatcherAgentLogic()
    dispatcher_core.dispatch_loop()

