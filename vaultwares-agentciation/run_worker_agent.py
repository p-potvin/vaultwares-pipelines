"""
Entrypoint for running a Worker Agent (ExtrovertAgent) as a process.
This script instantiates an ExtrovertAgent and starts it, so it can be monitored by the Lonely Manager.
"""
import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from extrovert_agent import ExtrovertAgent

def main(agent_id):
    agent = ExtrovertAgent(agent_id=agent_id)
    print(f"[Worker Agent: {agent_id}] Starting...")
    agent.start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print(f"[Worker Agent: {agent_id}] Shutting down.")
        agent._stop_event.set()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run a Worker Agent (ExtrovertAgent)")
    parser.add_argument('--id', type=str, required=True, help='Unique agent ID')
    args = parser.parse_args()
    main(args.id)
