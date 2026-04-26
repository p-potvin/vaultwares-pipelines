import os
import sys
import json
import time
import threading
import logging
import random
import argparse
import redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s | [%(levelname)s] | %(message)s")
logger = logging.getLogger("Worker")

class WorkerAgent:
    def __init__(self, agent_name, redis_host='localhost', redis_port=6379, db=0):
        self.agent_id = agent_name
        self.r = redis.Redis(host=redis_host, port=redis_port, db=db, decode_responses=True)
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe('tasks')
        self.current_status = 'RELAXING'
        self.current_task = None
        self.running = True

    def publish_status(self):
        "Announce current state so Dispatcher knows we exist"
        msg = {
            "agent": self.agent_id,
            "action": "STATUS",
            "task": self.current_task,
            "details": {"status": self.current_status}
        }
        self.r.publish("tasks", json.dumps(msg))

    def heartbeat(self):
        "Keep sending status every 3 seconds"
        while self.running:
            self.publish_status()
            time.sleep(3)

    def do_work(self, task_id, task_title):
        self.current_status = 'WORKING'
        self.current_task = task_id
        self.publish_status()
        
        # Log work started
        self.r.publish("tasks", json.dumps({
            "agent": self.agent_id,
            "action": "MSG",
            "task": task_id,
            "details": {"message": f"Started working on: {task_title}"}
        }))

        logger.info(f"[{self.agent_id}] Working on {task_id}: {task_title}...")
        
        # Simulate processing delay
        work_time = random.randint(4, 10)
        time.sleep(work_time)
        
        logger.info(f"[{self.agent_id}] Completed {task_id} after {work_time}s!")
        
        # Notify completion
        self.r.publish("tasks", json.dumps({
            "agent": self.agent_id,
            "action": "COMPLETE",
            "task": task_id,
            "details": {}
        }))

        # Reset state
        self.current_status = 'RELAXING'
        self.current_task = None
        self.publish_status()

    def listen_loop(self):
        logger.info(f"[{self.agent_id}] Listening for tasks...")
        for message in self.pubsub.listen():
            if not self.running:
                break
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    action = data.get('action')
                    target = data.get('target')
                    task_id = data.get('task')
                    
                    if action == 'ASSIGN' and target == self.agent_id:
                        title = data.get('details', {}).get('title', 'Unknown task')
                        # Start work in a new thread so we can keep listening
                        threading.Thread(target=self.do_work, args=(task_id, title), daemon=True).start()
                except json.JSONDecodeError:
                    pass

    def start(self):
        threading.Thread(target=self.heartbeat, daemon=True).start()
        self.listen_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, default=f"Worker-{random.randint(100,999)}", help="Agent ID")
    args = parser.parse_args()
    
    worker = WorkerAgent(agent_name=args.name)
    try:
        worker.start()
    except KeyboardInterrupt:
        worker.running = False
        logger.info("Worker shutting down.")
