import sys
import os
import time
import json
import redis
import re
import threading

# Add root and submodule to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "vaultwares-agentciation"))

from ai_model import TextProcessor, ImageProcessor, VideoProcessor, Workflow
import importlib
LonelyManager = importlib.import_module('vaultwares-agentciation.lonely_manager').LonelyManager
AgentStatus = importlib.import_module('vaultwares-agentciation.enums').AgentStatus

TASKS_FILE = "TASKS.md"

def parse_tasks():
    """Parses TASKS.md and returns a list of task objects."""
    if not os.path.exists(TASKS_FILE):
        return []
        
    tasks = []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines:
        # Match main tasks: N [Status] Title
        main_match = re.match(r"^(\d+)\s+\[(.*?)\]\s+(.*)$", line.strip())
        if main_match:
            tasks.append({
                "id": main_match.group(1),
                "status": main_match.group(2).strip(),
                "title": main_match.group(3).strip(),
                "type": "main"
            })
            continue
            
        # Match subtasks: Na [Status] Description (indented)
        sub_match = re.match(r"^\s+(\d+[a-z]+)\s+\[(.*?)\]\s+(.*)$", line)
        if sub_match:
            tasks.append({
                "id": sub_match.group(1),
                "status": sub_match.group(2).strip(),
                "title": sub_match.group(3).strip(),
                "type": "subtask"
            })
            
    return tasks

def update_task_status(task_id, new_status):
    """Updates the status of a specific task in TASKS.md."""
    if not os.path.exists(TASKS_FILE):
        return
        
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    new_lines = []
    status_map = {"WORKING": "~", "FINISHED": "x", "FREE": " "}
    char = status_map.get(new_status, new_status)
    
    for line in lines:
        # Pattern for main task: 1 [ ] Title
        # Pattern for subtask:   1a [ ] Title
        pattern = rf"^(\s*{re.escape(task_id)}\s+\[)(.*?)(\].*)$"
        match = re.match(pattern, line)
        if match:
            new_lines.append(f"{match.group(1)}{char}{match.group(3)}\n")
        else:
            new_lines.append(line)
            
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def main():
    print("--- 🚀 Initializing Generic Task Assignment System ---")
    
    r = redis.Redis(host='localhost', port=6379, db=0)
    channel = 'tasks'
    
    manager = LonelyManager(agent_id="manager-alpha")
    manager.start()
    
    # Initialize agent pool (Default 2)
    agents = [TextProcessor(), ImageProcessor()]
    
    print(f"\n--- 🤖 Live Agent Pool Status ---")
    for agent_id, info in manager._peer_registry.items():
        status = info.get("status", "OFFLINE")
        task_info = f" (Current Task: {info.get('task', 'None')})" if info.get('task') else ""
        print(f"[{agent_id}] Status: {status}{task_info}")
    
    print(f"\nAgents Online: {[a.agent_id for a in agents]}")
    time.sleep(2)

    try:
        while True:
            # Refresh Task List from TASKS.md
            current_tasks = parse_tasks()
            available_main_tasks = [t for t in current_tasks if t["type"] == "main" and t["status"] == " "]
            available_subtasks = [t for t in current_tasks if t["type"] == "subtask" and t["status"] == " "]
            
            # Print Dynamic Status Update (to stdout)
            print("\r" + " " * 80 + "\r", end="") # Clear line
            print(f"Agents Scanned: {len(manager._peer_registry)} | Tasks Free (M:{len(available_main_tasks)} S:{len(available_subtasks)})", end="", flush=True)

            # Check for RELAXING agents (WAITING_FOR_INPUT requires manual intervention/PR merge)
            for agent_id, info in manager._peer_registry.items():
                status = str(info.get("status", "")).upper()
                
                # We OMIT AgentStatus.WAITING_FOR_INPUT.value here because they 
                # must be manually handled (PR merged) before moving to RELAXING.
                if "RELAXING" in status and available_main_tasks:
                    task = available_main_tasks.pop(0)
                    print(f"\nAssigning {task['id']} to RELAXING agent {agent_id}")
                    r.publish(channel, json.dumps({
                        'agent': 'manager-alpha',
                        'action': 'ASSIGN',
                        'task': task['id'],
                        'target': agent_id,
                        'details': {'description': task['title']}
                    }))
                    update_task_status(task['id'], "WORKING")
                
                # Extra status check log (optional, only when interesting state occurs)
                if "WAITING_FOR_INPUT" in status:
                    # Logic to check for PR merge status could go here
                    pass

            time.sleep(1) # Frequency of check loop
            
    except KeyboardInterrupt:
        print("\n--- ⏹ Shutdown Requested ---")
        manager.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()

