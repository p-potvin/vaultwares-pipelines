"""
Abstract base class for all model wrappers.

Design goals
------------
* **Framework-agnostic** – the only mandatory interface is :meth:`generate`.
  Concrete sub-classes provide model-specific loading and inference logic.
* **Extensible** – sub-classes can override any hook (``_load_model``,
  ``_preprocess``, ``_postprocess``) without touching the public API.
* **Device-aware** – lazy device resolution via :class:`DeviceManager` so
  that the same code runs on CUDA, Apple MPS, and plain CPU.

Usage (direct)::

    from ai_model.core.model import BaseModelWrapper

    class MyWrapper(BaseModelWrapper):
        def _load_model(self): ...
        def generate(self, prompt, **kwargs): ...

Usage (via SmolVLM2Wrapper)::

    from ai_model import SmolVLM2Wrapper
    wrapper = SmolVLM2Wrapper()
    text = wrapper.generate("Describe this image", images=[pil_image])
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from PIL import Image

from ai_model.core.config import ModelConfig
from ai_model.utils.device import DeviceManager

logger = logging.getLogger(__name__)


class BaseModelWrapper(ABC):
    """Abstract wrapper that encapsulates any vision-language (or text-only) model.

    Parameters
    ----------
    config:
        A :class:`~ai_model.core.config.ModelConfig` instance.
        When *None* the class-level ``DEFAULT_CONFIG`` is used, which
        defaults to SmolVLM2-500M.
    """

    #: Sub-classes may set a class-level default so that
    #: ``MyWrapper()`` works with zero arguments.
    DEFAULT_CONFIG: ModelConfig = ModelConfig()

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        self.config = config or self.DEFAULT_CONFIG
        self.device_manager = DeviceManager(self.config.device)
        self.device = self.device_manager.resolve()
        self._model: Any = None
        self._processor: Any = None
        self._loaded: bool = False
        logger.debug(
            "Initialised %s with device=%s dtype=%s",
            self.__class__.__name__,
            self.device,
            self.config.dtype,
        )

    # ------------------------------------------------------------------ #
    # abstract interface                                                   #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def _load_model(self) -> None:
        """Load model weights and processor/tokeniser into memory.

        Called lazily on first use.  Assign results to ``self._model`` and
        ``self._processor``.
        """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        images: Optional[List[Image.Image]] = None,
        videos: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Run inference and return a text string.

        Parameters
        ----------
        prompt:
            The text instruction / question.
        images:
            Optional list of PIL images to include as visual context.
        videos:
            Optional list of video frame lists (each a ``List[PIL.Image]``).
        **kwargs:
            Extra generation parameters (override config values).

        Returns
        -------
        str
            The model's text response.
        """

    # ------------------------------------------------------------------ #
    # common helpers (may be overridden)                                  #
    # ------------------------------------------------------------------ #

    def load(self) -> "BaseModelWrapper":
        """Eagerly load the model.  Returns *self* for chaining.

        Example::

            wrapper = SmolVLM2Wrapper().load()
        """
        if not self._loaded:
            logger.info("Loading model %s …", self.config.model_id)
            self._load_model()
            self._loaded = True
            logger.info("Model loaded on %s", self.device)
        return self

    def unload(self) -> None:
        """Release model weights from memory (useful on edge devices)."""
        self._model = None
        self._processor = None
        self._loaded = False
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass

    def is_loaded(self) -> bool:
        """Return whether the model is currently in memory."""
        return self._loaded

    def __repr__(self) -> str:
        status = "loaded" if self._loaded else "unloaded"
        return (
            f"{self.__class__.__name__}("
            f"model_id={self.config.model_id!r}, "
            f"device={self.device!r}, "
            f"status={status!r})"
        )
