import sys
import os
import time
import json
import redis
import threading

# Add root and submodule to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "vaultwares_agentciation"))

from ai_model import TextProcessor, ImageProcessor, VideoProcessor, Workflow
import importlib
LonelyManager = importlib.import_module('vaultwares_agentciation.lonely_manager').LonelyManager

def main():
    print("--- 🚀 Initializing SPA Development Agent Team ---")
    
    # 1. Initialize the Backbone
    r = redis.Redis(host='localhost', port=6379, db=0)
    channel = 'tasks'
    
    # 2. Initialize the Manager
    manager = LonelyManager(agent_id="manager-alpha")
    manager.start()
    
    # 3. Initialize Processors (Agents)
    text_agent = TextProcessor()
    image_agent = ImageProcessor()
    video_agent = VideoProcessor()
    workflow_agent = Workflow(name="SPA-Deploy")
    
    print("\nAgents Online. Assigning Initial Tasks per plan_spa.md...\n")
    time.sleep(2) # Allow heartbeats to register

    # 4. Assign Tasks (Publish to Redis)
    # Task 1: Text Agent -> Design API Spec (1.1)
    r.publish(channel, json.dumps({
        'agent': 'manager-alpha',
        'action': 'ASSIGN',
        'task': 'API_DESIGN',
        'target': text_agent.agent_id,
        'details': {
            'step': '1.1',
            'description': 'Design OpenAPI spec for /workflows, /export, /backup endpoints.',
            'ref': 'plan_spa.md'
        }
    }))
    print(f"✅ Assigned API_DESIGN to {text_agent.agent_id}")

    # Task 2: Image Agent -> Design Wireframes (2.1)
    r.publish(channel, json.dumps({
        'agent': 'manager-alpha',
        'action': 'ASSIGN',
        'task': 'UI_WIREFRAMES',
        'target': image_agent.agent_id,
        'details': {
            'step': '2.1',
            'description': 'Create wireframes for category sidebar and workflow list.',
            'ref': 'plan_spa.md'
        }
    }))
    print(f"✅ Assigned UI_WIREFRAMES to {image_agent.agent_id}")

    # Task 3: Video Agent -> Demo Scenarios (2.4)
    r.publish(channel, json.dumps({
        'agent': 'manager-alpha',
        'action': 'ASSIGN',
        'task': 'VIDEO_DEMO_PLAN',
        'target': video_agent.agent_id,
        'details': {
            'step': 'N/A',
            'description': 'Plan screen recording scenario for the SPA workflow runner.',
            'ref': 'plan_spa.md'
        }
    }))
    print(f"✅ Assigned VIDEO_DEMO_PLAN to {video_agent.agent_id}")

    # 5. Monitor Status Update
    print("\nMonitoring Agent Status (Waiting for WORK signals)...")
    start_time = time.time()
    try:
        while time.time() - start_time < 20:
            print(f"\n[Status Check] T+{int(time.time() - start_time)}s")
            for peer_id, info in manager._peer_registry.items():
                print(f"  - {peer_id}: {info.get('status', 'OFFLINE')}")
            time.sleep(5)
    except KeyboardInterrupt:
        pass

    print("\nShutting down session...")
    manager.stop()
    text_agent.stop()
    image_agent.stop()
    video_agent.stop()
    workflow_agent.stop()

if __name__ == "__main__":
    main()
