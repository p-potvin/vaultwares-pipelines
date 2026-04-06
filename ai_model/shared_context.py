"""
Shared context and data structure for multi-agent workflows.
Validated with Pydantic for safety and extensibility.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class SharedContext(BaseModel):
    workflow_id: str = Field(..., description="Unique identifier for the workflow")
    agents: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific state/context")
    data: Dict[str, Any] = Field(default_factory=dict, description="Shared data accessible to all agents")
    errors: Optional[list] = Field(default_factory=list, description="Centralized error log")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata for workflow coordination")

    def add_agent_context(self, agent_name: str, context: Any):
        self.agents[agent_name] = context

    def log_error(self, error: str):
        self.errors.append(error)

    def add_data(self, key: str, value: Any):
        self.data[key] = value
