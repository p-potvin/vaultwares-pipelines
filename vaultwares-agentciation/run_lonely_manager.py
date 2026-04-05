"""
Entrypoint for running the Lonely Manager agent as a process.
This script instantiates the LonelyManager from vaultwares-agentciation and starts monitoring.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'vaultwares-agentciation')))
from lonely_manager import LonelyManager
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def alert_callback(alert):
    print(f"[ALERT] {alert['message']}")

if __name__ == "__main__":
    manager = LonelyManager(alert_callback=alert_callback)
    print("[Lonely Manager] Starting...")
    manager.start()
    try:
        while True:
            print("\n" + manager.get_project_status_report())
            time.sleep(60)
    except KeyboardInterrupt:
        print("[Lonely Manager] Shutting down.")
        manager._stop_event.set()
