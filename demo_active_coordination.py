import sys
import os
import time
import random

# Add root and submodule to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "vaultwares-agentciation"))

from ai_model import TextProcessor, ImageProcessor, VideoProcessor
from ai_model.core.smolvlm2 import GenericTextModelWrapper
import importlib
LonelyManager = importlib.import_module('vaultwares-agentciation.lonely_manager').LonelyManager

def main():
    print("--- Starting Demo: Active Task Coordination ---")
    
    # Use dummy model for demo to avoid heavy loads
    class DummyModel:
        def generate(self, *args, **kwargs):
            time.sleep(3) # Simulate work
            return "Generated content."
        def caption(self, *args, **kwargs):
            time.sleep(2)
            return "A sample image."

    model = DummyModel()
    
    # 1. Start Manager
    manager = LonelyManager(agent_id="manager-alpha")
    manager.start()
    
    # 2. Start Processors
    text_p = TextProcessor(model=model)
    image_p = ImageProcessor(model=model)
    
    print("Agents started. Waiting for heartbeats...")
    time.sleep(2)

    # 3. Simulate active work to show status changes
    print("\n[Action] Requesting Text Agent to enhance a prompt...")
    # This will trigger update_status(AgentStatus.WORKING)
    import threading
    def do_work():
        text_p.enhance_prompt("a beautiful digital art of a galaxy")
    
    work_thread = threading.Thread(target=do_work)
    work_thread.start()

    # 4. Monitor the registry while work is happening
    start_time = time.time()
    while time.time() - start_time < 10:
        print(f"\n[System Check] Time: {int(time.time() - start_time)}s")
        for peer_id, info in manager._peer_registry.items():
            status = info.get('status', 'UNKNOWN')
            print(f"  - {peer_id}: {status}")
        time.sleep(2)

    print("\nShutting down...")
    manager.stop()
    text_p.stop()
    image_p.stop()

if __name__ == "__main__":
    main()
