"""
Video-level manipulation functions.

All functions take and return lists of :class:`PIL.Image.Image` frames so
that they compose naturally with the image manipulation functions and the
SmolVLM2 inference pipeline.

Quick reference
---------------
* :func:`trim_frames`       – keep a sub-range of frames
* :func:`resize_frames`     – resize every frame
* :func:`reverse_frames`    – play the video backwards
* :func:`apply_frame_effect` – apply any image effect to every frame
* :func:`add_frame_overlay`  – add a semi-transparent overlay to each frame
* :func:`stabilize_frames`   – simple motion stabilisation via feature matching
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Tuple

import numpy as np
from PIL import Image


def trim_frames(
    frames: List[Image.Image],
    start: int = 0,
    end: Optional[int] = None,
) -> List[Image.Image]:
    """Return a slice of *frames* from index *start* to *end*.

    Parameters
    ----------
    frames:
        Ordered list of PIL frames.
    start:
        First frame index (inclusive, 0-based).
    end:
        Last frame index (exclusive).  ``None`` means end of video.

    Returns
    -------
    List[PIL.Image.Image]
        Trimmed frame list.

    Example::

        clip = trim_frames(frames, start=30, end=90)  # frames 30–89
    """
    return frames[start:end]


def resize_frames(
    frames: List[Image.Image],
    width: int,
    height: int,
) -> List[Image.Image]:
    """Resize every frame to *width* × *height*.

    Parameters
    ----------
    frames:
        Input frames.
    width, height:
        Target dimensions.

    Returns
    -------
    List[PIL.Image.Image]
        Resized frames.

    Example::

        small_frames = resize_frames(frames, 320, 240)
    """
    return [f.resize((width, height), resample=Image.LANCZOS) for f in frames]


def reverse_frames(frames: List[Image.Image]) -> List[Image.Image]:
    """Reverse the frame order to play the video backwards.

    Parameters
    ----------
    frames:
        Input frames.

    Returns
    -------
    List[PIL.Image.Image]
        Reversed frames.

    Example::

        backwards = reverse_frames(frames)
    """
    return frames[::-1]


def apply_frame_effect(
    frames: List[Image.Image],
    effect: Callable[[Image.Image], Image.Image],
) -> List[Image.Image]:
    """Apply an arbitrary image transformation to every frame.

    Parameters
    ----------
    frames:
        Input frames.
    effect:
        Callable that takes and returns a PIL image.  Any function from
        :mod:`ai_model.image.manipulation` works here.

    Returns
    -------
    List[PIL.Image.Image]
        Processed frames.

    Example::

        from ai_model.image.manipulation import sharpen
        sharp_frames = apply_frame_effect(frames, lambda f: sharpen(f, percent=150))
    """
    return [effect(frame) for frame in frames]


def add_frame_overlay(
    frames: List[Image.Image],
    overlay: Image.Image,
    alpha: float = 0.3,
    position: Tuple[int, int] = (0, 0),
) -> List[Image.Image]:
    """Composite a semi-transparent *overlay* onto every frame.

    Useful for watermarks, logos, or HUD elements.

    Parameters
    ----------
    frames:
        Input frames.
    overlay:
        PIL image to overlay (converted to RGBA internally).
    alpha:
        Overlay opacity (0.0 = invisible, 1.0 = fully opaque).
    position:
        ``(x, y)`` top-left pixel where the overlay is pasted.

    Returns
    -------
    List[PIL.Image.Image]
        Frames with overlay composited.

    Example::

        logo = Image.open("logo.png")
        watermarked = add_frame_overlay(frames, logo, alpha=0.2)
    """
    overlay_rgba = overlay.convert("RGBA")
    # adjust alpha
    r, g, b, a = overlay_rgba.split()
    a = a.point(lambda p: int(p * alpha))
    overlay_rgba = Image.merge("RGBA", (r, g, b, a))

    result = []
    for frame in frames:
        base = frame.convert("RGBA")
        base.paste(overlay_rgba, position, mask=overlay_rgba)
        result.append(base.convert("RGB"))
    return result


def stabilize_frames(
    frames: List[Image.Image],
) -> List[Image.Image]:
    """Reduce camera shake via affine motion estimation between consecutive frames.

    Uses OpenCV's ``estimateAffinePartial2D`` with ORB feature matching.
    Falls back gracefully if OpenCV is not installed.

    Parameters
    ----------
    frames:
        Input frames (should all be the same size).

    Returns
    -------
    List[PIL.Image.Image]
        Stabilised frames.

    Example::

        stable = stabilize_frames(shaky_frames)
    """
    try:
        import cv2
    except ImportError:
        import warnings
        warnings.warn(
            "opencv-python is required for stabilize_frames.  Returning frames unchanged.",
            stacklevel=2,
        )
        return frames

    if len(frames) < 2:
        return frames

    result = [frames[0]]
    ref_gray = cv2.cvtColor(np.array(frames[0].convert("RGB")), cv2.COLOR_RGB2GRAY)
    orb = cv2.ORB_create(500)
    kp_ref, des_ref = orb.detectAndCompute(ref_gray, None)

    for frame in frames[1:]:
        gray = cv2.cvtColor(np.array(frame.convert("RGB")), cv2.COLOR_RGB2GRAY)
        kp, des = orb.detectAndCompute(gray, None)

        if des is None or des_ref is None:
            result.append(frame)
            continue

        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = matcher.match(des_ref, des)
        matches = sorted(matches, key=lambda m: m.distance)[:50]

        if len(matches) < 4:
            result.append(frame)
            continue

        src_pts = np.float32([kp_ref[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        M, _ = cv2.estimateAffinePartial2D(dst_pts, src_pts, method=cv2.RANSAC)
        if M is None:
            result.append(frame)
            continue

        h, w = gray.shape
        bgr = cv2.cvtColor(np.array(frame.convert("RGB")), cv2.COLOR_RGB2BGR)
        stabilised_bgr = cv2.warpAffine(bgr, M, (w, h))
        stabilised_rgb = cv2.cvtColor(stabilised_bgr, cv2.COLOR_BGR2RGB)
        result.append(Image.fromarray(stabilised_rgb))

    return result
