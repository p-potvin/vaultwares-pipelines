# redis_coordination.py
"""
Reusable Redis-based coordination module for multi-agent collaboration.
Standardizes task claim, completion, and status messages.
"""
import redis
import threading
import json

class RedisCoordinator:
    def __init__(self, agent_id, channel='tasks', host='localhost', port=6379, db=0):
        self.agent_id = agent_id
        self.channel = channel
        self.r = redis.Redis(host=host, port=port, db=db)
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe(channel)
        self.listener_thread = None
        self.running = False

    def publish(self, action, task, details=None):
        msg = {
            'agent': self.agent_id,
            'action': action,  # e.g., CLAIM, COMPLETE, STATUS, BLOCKED
            'task': task,
            'details': details or {}
        }
        self.r.publish(self.channel, json.dumps(msg))

    def listen(self, callback):
        def _listen():
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        callback(data)
                    except Exception:
                        pass
        self.running = True
        self.listener_thread = threading.Thread(target=_listen, daemon=True)
        self.listener_thread.start()

    def stop(self):
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1)

# Example integration:
# from redis_coordination import RedisCoordinator
# coordinator = RedisCoordinator(agent_id='agent1')
# coordinator.publish('CLAIM', 'feature-x')
# coordinator.listen(lambda msg: print('Received:', msg))
