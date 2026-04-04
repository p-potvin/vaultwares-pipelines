"""
SmolVLM2 Wrapper – multi-modal manipulation toolkit
====================================================

Top-level exports for the most commonly used classes and helpers so that
callers only need a single import::

    from smolvlm2_wrapper import SmolVLM2Wrapper, ImageProcessor, VideoProcessor, TextProcessor

See README.md for full usage examples and workflow documentation.
"""

from smolvlm2_wrapper.core.model import BaseModelWrapper
from smolvlm2_wrapper.core.smolvlm2 import SmolVLM2Wrapper
from smolvlm2_wrapper.image.processor import ImageProcessor
from smolvlm2_wrapper.video.processor import VideoProcessor
from smolvlm2_wrapper.text.processor import TextProcessor
from smolvlm2_wrapper.workflows.base import Workflow
from smolvlm2_wrapper.utils.device import DeviceManager

__version__ = "0.1.0"

__all__ = [
    "BaseModelWrapper",
    "SmolVLM2Wrapper",
    "ImageProcessor",
    "VideoProcessor",
    "TextProcessor",
    "Workflow",
    "DeviceManager",
]
