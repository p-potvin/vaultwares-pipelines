"""Core model abstractions and AIModel-specific integration."""

from ai_model.core.model import BaseModelWrapper
from ai_model.core.text_model import TextModelWrapper
from ai_model.core.config import ModelConfig

__all__ = ["BaseModelWrapper", "TextModelWrapper", "ModelConfig"]
