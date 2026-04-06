"""
I/O helpers for images and videos.

All public functions accept both file-paths (``str`` / ``pathlib.Path``) and
already-loaded objects so that callers are never forced to manage loading
themselves.

Usage::

    from ai_model.utils.io import load_image, save_image

    img = load_image("photo.jpg")
    save_image(img, "/tmp/out.png")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Union

from PIL import Image


# --------------------------------------------------------------------------- #
# image helpers                                                                #
# --------------------------------------------------------------------------- #

def load_image(source: Union[str, Path, Image.Image]) -> Image.Image:
    """Load a PIL image from a file path or pass through an existing Image.

    Parameters
    ----------
    source:
        File path string, :class:`pathlib.Path`, or an already-loaded
        :class:`PIL.Image.Image`.

    Returns
    -------
    PIL.Image.Image
        Image in RGB mode.

    Example::

        from ai_model.utils.io import load_image
        img = load_image("photo.jpg")
    """
    if isinstance(source, Image.Image):
        return source.convert("RGB")
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    return Image.open(path).convert("RGB")


def save_image(image: Image.Image, dest: Union[str, Path]) -> Path:
    """Save a PIL image to *dest*, creating parent directories if needed.

    Parameters
    ----------
    image:
        PIL image to save.
    dest:
        Destination file path.  The format is inferred from the extension
        (e.g. ``.png``, ``.jpg``).

    Returns
    -------
    pathlib.Path
        Absolute path to the saved file.

    Example::

        save_image(processed_image, "output/result.png")
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)
    return dest.resolve()


# --------------------------------------------------------------------------- #
# video helpers                                                                #
# --------------------------------------------------------------------------- #

def load_video(
    source: Union[str, Path],
    max_frames: int = 0,
) -> List[Image.Image]:
    """Load a video file and return its frames as PIL images.

    Parameters
    ----------
    source:
        Path to a video file (any format supported by OpenCV).
    max_frames:
        Maximum number of frames to load.  ``0`` means load all frames
        (use with caution for long videos).

    Returns
    -------
    List[PIL.Image.Image]
        Ordered list of RGB frames.

    Raises
    ------
    ImportError
        If ``opencv-python`` is not installed.
    FileNotFoundError
        If the video file does not exist.

    Example::

        frames = load_video("clip.mp4", max_frames=16)
    """
    try:
        import cv2
    except ImportError as exc:
        raise ImportError(
            "opencv-python is required to load videos.  "
            "Install it with: pip install opencv-python"
        ) from exc

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {path}")

    cap = cv2.VideoCapture(str(path))
    frames: List[Image.Image] = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(rgb))
        if max_frames and len(frames) >= max_frames:
            break
    cap.release()
    return frames


def save_video(
    frames: List[Image.Image],
    dest: Union[str, Path],
    fps: float = 24.0,
    codec: str = "mp4v",
) -> Path:
    """Encode a list of PIL frames into a video file.

    Parameters
    ----------
    frames:
        Ordered list of PIL images (all must be the same size).
    dest:
        Output file path (e.g. ``"output/result.mp4"``).
    fps:
        Frames per second of the output video.
    codec:
        FourCC codec string (default ``"mp4v"`` for MP4).

    Returns
    -------
    pathlib.Path
        Absolute path to the saved video.

    Raises
    ------
    ImportError
        If ``opencv-python`` is not installed.
    ValueError
        If *frames* is empty.

    Example::

        save_video(edited_frames, "output/result.mp4", fps=30)
    """
    try:
        import cv2
    except ImportError as exc:
        raise ImportError(
            "opencv-python is required to save videos.  "
            "Install it with: pip install opencv-python"
        ) from exc

    if not frames:
        raise ValueError("frames must not be empty.")

    import numpy as np

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    w, h = frames[0].size
    fourcc = cv2.VideoWriter_fourcc(*codec)
    writer = cv2.VideoWriter(str(dest), fourcc, fps, (w, h))
    for frame in frames:
        bgr = cv2.cvtColor(np.array(frame.convert("RGB")), cv2.COLOR_RGB2BGR)
        writer.write(bgr)
    writer.release()
    return dest.resolve()
