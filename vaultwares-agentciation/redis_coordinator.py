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
            'action': action,
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
