import sys
import os
import time

# Add root and submodule to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "vaultwares_agentciation"))

from ai_model import TextProcessor, ImageProcessor, VideoProcessor
import importlib
LonelyManager = importlib.import_module('vaultwares_agentciation.lonely_manager').LonelyManager

def main():
    print("--- Initializing Multi-Agent System (Standardized Coordination) ---")
    
    # Initialize Manager
    manager = LonelyManager(agent_id="manager-alpha")
    manager.start()
    print(f"Manager {manager.agent_id} started.")
    
    # Initialize Processors (they now inherit from ExtrovertAgent and start automatically)
    text_p = TextProcessor()
    image_p = ImageProcessor()
    video_p = VideoProcessor()
    
    print(f"Text Agent: {text_p.agent_id}")
    print(f"Image Agent: {image_p.agent_id}")
    print(f"Video Agent: {video_p.agent_id}")
    
    print("\n--- Monitoring Heartbeats (Press Ctrl+C to stop) ---")
    try:
        while True:
            # The agents are running in background threads
            # Manager will log peer discoveries via Redis
            time.sleep(10)
            print(f"\n[System Check] Peer Registry Size: {len(manager._peer_registry)}")
            for peer_id, info in manager._peer_registry.items():
                print(f"  - {peer_id}: {info.get('status', 'UNKNOWN')}")
                
    except KeyboardInterrupt:
        print("\nStopping agents...")
        text_p.stop()
        image_p.stop()
        video_p.stop()
        manager.stop()
        print("System shutdown complete.")

if __name__ == "__main__":
    main()
