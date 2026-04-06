"""Video processing sub-package."""

from ai_model.video.processor import VideoProcessor
from ai_model.video.manipulation import (
    trim_frames,
    resize_frames,
    reverse_frames,
    apply_frame_effect,
    add_frame_overlay,
    stabilize_frames,
)
from ai_model.video.utils import (
    sample_frames,
    frames_to_gif,
    add_audio,
)

__all__ = [
    "VideoProcessor",
    # manipulation
    "trim_frames", "resize_frames", "reverse_frames",
    "apply_frame_effect", "add_frame_overlay", "stabilize_frames",
    # utils
    "sample_frames", "frames_to_gif", "add_audio",
]
