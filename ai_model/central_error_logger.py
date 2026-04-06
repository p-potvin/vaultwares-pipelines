"""
Central error log and feedback loop for multi-agent workflows.
Subscribes to error events and maintains a persistent error log.
"""
from ai_model.event_bus import EventBus
from ai_model.shared_context import SharedContext

class CentralErrorLogger:
    def __init__(self, shared_context: SharedContext):
        self.shared_context = shared_context
        EventBus.subscribe('error', self.handle_error)

    def handle_error(self, data):
        agent = data.get('agent', 'unknown')
        errors = data.get('errors', [])
        for err in errors:
            self.shared_context.log_error(f"[{agent}] {err}")

    def get_error_log(self):
        return self.shared_context.errors or []
