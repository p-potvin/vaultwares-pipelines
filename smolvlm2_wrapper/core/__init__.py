"""Core model abstractions and SmolVLM2-specific integration."""

from smolvlm2_wrapper.core.model import BaseModelWrapper
from smolvlm2_wrapper.core.smolvlm2 import SmolVLM2Wrapper
from smolvlm2_wrapper.core.config import ModelConfig

__all__ = ["BaseModelWrapper", "SmolVLM2Wrapper", "ModelConfig"]
