"""
Validation and error reporting utilities for multi-agent workflows.
"""
from typing import Any, Dict, List
from pydantic import ValidationError
from smolvlm2_wrapper.shared_context import SharedContext

class ValidationUtils:
    @staticmethod
    def validate_context(context_model, data: Dict) -> List[str]:
        """Validate data against a Pydantic model. Returns list of error messages."""
        try:
            context_model(**data)
            return []
        except ValidationError as e:
            return [err['msg'] for err in e.errors()]

    @staticmethod
    def report_error(shared_context: SharedContext, agent_name: str, error: str):
        shared_context.log_error(f"[{agent_name}] {error}")

    @staticmethod
    def get_errors(shared_context: SharedContext) -> List[str]:
        return shared_context.errors or []
