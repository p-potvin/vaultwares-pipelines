"""
Base interface for agents to interact with the shared context in multi-agent workflows.
"""
from typing import Any
from smolvlm2_wrapper.shared_context import SharedContext

class AgentInterface:
    def __init__(self, name: str, shared_context: SharedContext):
        self.name = name
        self.shared_context = shared_context

    def get_context(self) -> Any:
        return self.shared_context.agents.get(self.name, {})

    def set_context(self, context: Any):
        self.shared_context.add_agent_context(self.name, context)

    def get_shared_data(self, key: str) -> Any:
        return self.shared_context.data.get(key)

    def set_shared_data(self, key: str, value: Any):
        self.shared_context.add_data(key, value)

    def log_error(self, error: str):
        self.shared_context.log_error(f"[{self.name}] {error}")
