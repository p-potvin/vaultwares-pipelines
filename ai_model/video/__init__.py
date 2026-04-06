"""Video processing sub-package."""

from smolvlm2_wrapper.video.processor import VideoProcessor
from smolvlm2_wrapper.video.manipulation import (
    trim_frames,
    resize_frames,
    reverse_frames,
    apply_frame_effect,
    add_frame_overlay,
    stabilize_frames,
)
from smolvlm2_wrapper.video.utils import (
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
