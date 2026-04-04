"""
Mask creation and application utilities.

A *mask* is a greyscale PIL image (mode ``"L"``) where:
* **255 (white)** = fully opaque / region of interest
* **0 (black)**   = fully transparent / background

All functions return new images and never mutate their inputs.

Quick reference
---------------
* :func:`create_mask`         – blank mask (all black or all white)
* :func:`create_rect_mask`    – rectangular region mask
* :func:`create_circular_mask` – circular / elliptical region mask
* :func:`apply_mask`          – composite image through mask
* :func:`invert_mask`         – swap foreground/background
* :func:`feather_mask`        – soften mask edges with Gaussian blur
* :func:`mask_from_color`     – derive mask from a specific colour range
"""

from __future__ import annotations

from typing import Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def create_mask(
    width: int,
    height: int,
    fill: int = 0,
) -> Image.Image:
    """Create a blank greyscale mask.

    Parameters
    ----------
    width, height:
        Mask dimensions in pixels.
    fill:
        Initial pixel value (0 = black / transparent, 255 = white / opaque).

    Returns
    -------
    PIL.Image.Image
        New ``"L"`` mode image.

    Example::

        mask = create_mask(512, 512)          # all-black
        mask = create_mask(512, 512, fill=255) # all-white
    """
    return Image.new("L", (width, height), fill)


def create_rect_mask(
    width: int,
    height: int,
    box: Tuple[int, int, int, int],
    value: int = 255,
) -> Image.Image:
    """Create a mask with a filled rectangle.

    Parameters
    ----------
    width, height:
        Mask dimensions.
    box:
        ``(left, top, right, bottom)`` of the rectangle to fill.
    value:
        Fill value inside the rectangle (default 255 = white).

    Returns
    -------
    PIL.Image.Image
        Greyscale mask.

    Example::

        mask = create_rect_mask(512, 512, (100, 100, 400, 400))
    """
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(box, fill=value)
    return mask


def create_circular_mask(
    width: int,
    height: int,
    center: Tuple[int, int],
    radius: int,
    value: int = 255,
) -> Image.Image:
    """Create a mask with a filled circle (or ellipse if radii differ).

    Parameters
    ----------
    width, height:
        Mask dimensions.
    center:
        ``(cx, cy)`` centre of the circle.
    radius:
        Radius in pixels.
    value:
        Fill value (default 255 = white).

    Returns
    -------
    PIL.Image.Image
        Greyscale mask.

    Example::

        mask = create_circular_mask(512, 512, center=(256, 256), radius=100)
    """
    cx, cy = center
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=value,
    )
    return mask


def apply_mask(
    image: Image.Image,
    mask: Image.Image,
    background: Union[Tuple[int, int, int], Image.Image] = (0, 0, 0),
) -> Image.Image:
    """Composite *image* over *background* using *mask* as the alpha channel.

    Where the mask is white (255) the image is shown; where the mask is
    black (0) the background shows through.

    Parameters
    ----------
    image:
        Foreground PIL image.
    mask:
        ``"L"`` mode mask.
    background:
        Either an RGB colour tuple or another PIL image of the same size.

    Returns
    -------
    PIL.Image.Image
        Composited RGB image.

    Example::

        result = apply_mask(photo, mask, background=(128, 128, 128))
    """
    img_rgb = image.convert("RGB")

    if isinstance(background, Image.Image):
        bg = background.convert("RGB").resize(img_rgb.size)
    else:
        bg = Image.new("RGB", img_rgb.size, background)

    # resize mask to match image if sizes differ
    if mask.size != img_rgb.size:
        mask = mask.resize(img_rgb.size, resample=Image.LANCZOS)

    result = Image.composite(img_rgb, bg, mask)
    return result


def invert_mask(mask: Image.Image) -> Image.Image:
    """Invert a mask so that foreground becomes background and vice versa.

    Parameters
    ----------
    mask:
        ``"L"`` mode mask.

    Returns
    -------
    PIL.Image.Image
        Inverted mask.

    Example::

        inv = invert_mask(mask)
    """
    arr = np.array(mask)
    return Image.fromarray(255 - arr)


def feather_mask(
    mask: Image.Image,
    radius: float = 5.0,
) -> Image.Image:
    """Soften the edges of *mask* using Gaussian blur.

    This produces a smooth, anti-aliased transition between the masked
    and unmasked regions.

    Parameters
    ----------
    mask:
        ``"L"`` mode mask.
    radius:
        Blur radius (higher = softer edges).

    Returns
    -------
    PIL.Image.Image
        Feathered mask.

    Example::

        soft_mask = feather_mask(mask, radius=10)
    """
    return mask.filter(ImageFilter.GaussianBlur(radius=radius))


def mask_from_color(
    image: Image.Image,
    target_color: Tuple[int, int, int],
    tolerance: int = 30,
) -> Image.Image:
    """Create a mask that selects pixels close to *target_color*.

    Uses Euclidean distance in RGB space.  Pixels within *tolerance* of
    the target colour become white (255); others become black (0).

    Parameters
    ----------
    image:
        Input RGB image.
    target_color:
        ``(R, G, B)`` reference colour.
    tolerance:
        Maximum Euclidean distance from *target_color* to be included
        in the mask.

    Returns
    -------
    PIL.Image.Image
        ``"L"`` mode binary mask.

    Example::

        # Select all green-ish pixels
        mask = mask_from_color(img, target_color=(0, 200, 0), tolerance=50)
    """
    arr = np.array(image.convert("RGB"), dtype=np.float32)
    target = np.array(target_color, dtype=np.float32)
    dist = np.linalg.norm(arr - target, axis=-1)
    binary = (dist <= tolerance).astype(np.uint8) * 255
    return Image.fromarray(binary, mode="L")
