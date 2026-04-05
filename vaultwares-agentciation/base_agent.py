import threading
import time
from redis_coordinator import RedisCoordinator
from enums import AgentStatus

class AgentBase:
    def __init__(self, agent_id, channel='tasks', redis_host='localhost', redis_port=6379, redis_db=0):
        self.agent_id = agent_id
        self.status = AgentStatus.WAITING_FOR_INPUT
        self.coordinator = RedisCoordinator(agent_id, channel, redis_host, redis_port, redis_db)
        self.heartbeat_interval = 5
        self._stop_event = threading.Event()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)

    def start(self):
        self._heartbeat_thread.start()

    def _heartbeat_loop(self):
        while not self._stop_event.is_set():
            self.send_heartbeat()
            time.sleep(self.heartbeat_interval)

    def send_heartbeat(self):
        self.coordinator.publish('HEARTBEAT', 'heartbeat', {'status': self.status.value})

    def update_status(self, status):
        self.status = status
        self.coordinator.publish('STATUS', 'status_update', {'status': self.status.value})

    def stop(self):
        self._stop_event.set()
        self._heartbeat_thread.join(timeout=1)
