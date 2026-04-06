"""
Configuration management for model wrappers.

Usage::

    from ai_model.core.config import ModelConfig

    cfg = ModelConfig(
        model_id="HuggingFaceTB/SmolVLM2-500M-Video-Instruct",
        device="cpu",
        dtype="float32",
        max_new_tokens=256,
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ModelConfig:
    """Unified configuration for any model wrapper.

    Attributes
    ----------
    model_id:
        HuggingFace model ID or local path.
    device:
        Target device string.  ``"auto"`` lets the wrapper choose the best
        available device (CUDA → MPS → CPU).
    dtype:
        Floating-point precision.  Use ``"float16"`` or ``"bfloat16"`` to
        reduce VRAM/RAM usage on capable hardware; fall back to
        ``"float32"`` for pure-CPU or older GPUs.
    max_new_tokens:
        Maximum number of tokens to generate per call.
    do_sample:
        Whether to use sampling (``True``) or greedy decoding (``False``).
    temperature:
        Sampling temperature; only used when ``do_sample=True``.
    top_p:
        Top-p nucleus sampling parameter; only used when ``do_sample=True``.
    low_memory:
        Enable extra memory-saving options (CPU offloading, reduced cache).
        Recommended for devices with < 4 GB RAM.
    cache_dir:
        Override default HuggingFace cache directory.
    extra:
        Arbitrary extra kwargs forwarded verbatim to the underlying
        ``from_pretrained`` call.
    """

    model_id: str = "HuggingFaceTB/SmolVLM2-500M-Video-Instruct"
    device: str = "auto"
    dtype: str = "float32"
    max_new_tokens: int = 256
    do_sample: bool = False
    temperature: float = 1.0
    top_p: float = 1.0
    low_memory: bool = False
    cache_dir: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # helpers                                                              #
    # ------------------------------------------------------------------ #

    def generation_kwargs(self) -> dict:
        """Return keyword arguments suitable for a ``model.generate()`` call."""
        kwargs = {"max_new_tokens": self.max_new_tokens}
        if self.do_sample:
            kwargs["do_sample"] = True
            kwargs["temperature"] = self.temperature
            kwargs["top_p"] = self.top_p
        return kwargs
