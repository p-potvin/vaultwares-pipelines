"""
Core image manipulation functions.

All functions operate on :class:`PIL.Image.Image` objects and return a *new*
image (inputs are never mutated).  NumPy arrays are used internally for
pixel-level operations.

Quick reference
---------------
* :func:`resize`               – resize to target dimensions
* :func:`crop`                 – crop a rectangular region
* :func:`rotate`               – rotate by angle
* :func:`flip`                 – flip horizontally or vertically
* :func:`sharpen`              – apply unsharp-mask sharpening
* :func:`blur`                 – Gaussian blur
* :func:`adjust_brightness`    – multiply pixel brightness
* :func:`adjust_contrast`      – scale contrast around mean
* :func:`adjust_saturation`    – change colour saturation
* :func:`apply_filter`         – apply a named convolution filter
* :func:`upscale`              – integer super-resolution via Lanczos
* :func:`convert_color_space`  – convert between RGB/RGBA/L/HSV
* :func:`add_noise`            – add Gaussian noise
* :func:`denoise`              – simple median denoising
"""

from __future__ import annotations

from typing import Literal, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# --------------------------------------------------------------------------- #
# resize / crop / transform                                                    #
# --------------------------------------------------------------------------- #

def resize(
    image: Image.Image,
    width: int,
    height: int,
    resample: int = Image.LANCZOS,
) -> Image.Image:
    """Resize *image* to (*width*, *height*).

    Parameters
    ----------
    image:
        Input PIL image.
    width:
        Target width in pixels.
    height:
        Target height in pixels.
    resample:
        Resampling filter (default :attr:`PIL.Image.LANCZOS`).

    Returns
    -------
    PIL.Image.Image
        Resized image.

    Example::

        from ai_model.image.manipulation import resize
        small = resize(img, 320, 240)
    """
    return image.resize((width, height), resample=resample)


def crop(
    image: Image.Image,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> Image.Image:
    """Crop a rectangular region from *image*.

    Parameters
    ----------
    image:
        Input PIL image.
    left, top, right, bottom:
        Pixel coordinates of the crop box (inclusive left/top, exclusive
        right/bottom – same convention as :meth:`PIL.Image.crop`).

    Returns
    -------
    PIL.Image.Image
        Cropped sub-image.

    Example::

        face = crop(img, 100, 50, 400, 350)
    """
    return image.crop((left, top, right, bottom))


def rotate(
    image: Image.Image,
    angle: float,
    expand: bool = True,
    fill_color: Union[Tuple[int, int, int], int] = (0, 0, 0),
) -> Image.Image:
    """Rotate *image* counter-clockwise by *angle* degrees.

    Parameters
    ----------
    image:
        Input PIL image.
    angle:
        Rotation angle in degrees (counter-clockwise).
    expand:
        If ``True`` the output canvas is expanded so the full rotated image
        is visible.
    fill_color:
        Background colour used to fill empty areas after rotation.

    Returns
    -------
    PIL.Image.Image
        Rotated image.

    Example::

        tilted = rotate(img, 15)
    """
    return image.rotate(angle, expand=expand, fillcolor=fill_color)


def flip(
    image: Image.Image,
    direction: Literal["horizontal", "vertical"] = "horizontal",
) -> Image.Image:
    """Flip *image* horizontally or vertically.

    Parameters
    ----------
    image:
        Input PIL image.
    direction:
        ``"horizontal"`` (mirror) or ``"vertical"`` (upside-down).

    Returns
    -------
    PIL.Image.Image
        Flipped image.

    Example::

        mirrored = flip(img, "horizontal")
    """
    if direction == "horizontal":
        return image.transpose(Image.FLIP_LEFT_RIGHT)
    elif direction == "vertical":
        return image.transpose(Image.FLIP_TOP_BOTTOM)
    else:
        raise ValueError(f"direction must be 'horizontal' or 'vertical', got {direction!r}")


# --------------------------------------------------------------------------- #
# enhancement                                                                  #
# --------------------------------------------------------------------------- #

def sharpen(
    image: Image.Image,
    radius: float = 2.0,
    percent: int = 150,
    threshold: int = 3,
) -> Image.Image:
    """Sharpen *image* using an unsharp-mask filter.

    Parameters
    ----------
    image:
        Input PIL image.
    radius:
        Blur radius used to compute the unsharp mask.
    percent:
        Strength of the sharpening effect (100 = no change, > 100 = sharper).
    threshold:
        Minimum brightness difference between original and blurred pixel
        required before sharpening is applied.

    Returns
    -------
    PIL.Image.Image
        Sharpened image.

    Example::

        crisp = sharpen(img, radius=2, percent=200)
    """
    return image.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))


def blur(
    image: Image.Image,
    radius: float = 2.0,
) -> Image.Image:
    """Apply Gaussian blur to *image*.

    Parameters
    ----------
    image:
        Input PIL image.
    radius:
        Blur radius (higher → more blurred).

    Returns
    -------
    PIL.Image.Image
        Blurred image.

    Example::

        soft = blur(img, radius=5)
    """
    return image.filter(ImageFilter.GaussianBlur(radius=radius))


def adjust_brightness(
    image: Image.Image,
    factor: float,
) -> Image.Image:
    """Multiply pixel brightness by *factor*.

    Parameters
    ----------
    image:
        Input PIL image.
    factor:
        ``1.0`` → unchanged, ``< 1.0`` → darker, ``> 1.0`` → brighter.

    Returns
    -------
    PIL.Image.Image
        Brightness-adjusted image.

    Example::

        brighter = adjust_brightness(img, 1.5)
    """
    return ImageEnhance.Brightness(image).enhance(factor)


def adjust_contrast(
    image: Image.Image,
    factor: float,
) -> Image.Image:
    """Scale contrast around the image mean.

    Parameters
    ----------
    image:
        Input PIL image.
    factor:
        ``1.0`` → unchanged, ``0.0`` → solid grey, ``> 1.0`` → more contrast.

    Returns
    -------
    PIL.Image.Image
        Contrast-adjusted image.

    Example::

        vivid = adjust_contrast(img, 1.3)
    """
    return ImageEnhance.Contrast(image).enhance(factor)


def adjust_saturation(
    image: Image.Image,
    factor: float,
) -> Image.Image:
    """Change colour saturation.

    Parameters
    ----------
    image:
        Input PIL image.
    factor:
        ``1.0`` → unchanged, ``0.0`` → greyscale, ``> 1.0`` → more vivid.

    Returns
    -------
    PIL.Image.Image
        Saturation-adjusted image.

    Example::

        grey = adjust_saturation(img, 0.0)
        vivid = adjust_saturation(img, 2.0)
    """
    return ImageEnhance.Color(image).enhance(factor)


def apply_filter(
    image: Image.Image,
    name: Literal[
        "edge_enhance", "emboss", "find_edges", "smooth", "detail", "contour"
    ],
) -> Image.Image:
    """Apply a named convolution filter to *image*.

    Parameters
    ----------
    image:
        Input PIL image.
    name:
        One of ``"edge_enhance"``, ``"emboss"``, ``"find_edges"``,
        ``"smooth"``, ``"detail"``, ``"contour"``.

    Returns
    -------
    PIL.Image.Image
        Filtered image.

    Example::

        edges = apply_filter(img, "find_edges")
    """
    filter_map = {
        "edge_enhance": ImageFilter.EDGE_ENHANCE,
        "emboss": ImageFilter.EMBOSS,
        "find_edges": ImageFilter.FIND_EDGES,
        "smooth": ImageFilter.SMOOTH,
        "detail": ImageFilter.DETAIL,
        "contour": ImageFilter.CONTOUR,
    }
    if name not in filter_map:
        raise ValueError(f"Unknown filter {name!r}. Choose from {list(filter_map)}")
    return image.filter(filter_map[name])


def upscale(
    image: Image.Image,
    scale: int = 2,
) -> Image.Image:
    """Upscale *image* by an integer *scale* factor using Lanczos resampling.

    For best quality use scale 2 or 4.  Very large scales may produce
    artefacts; consider a dedicated super-resolution model for scale > 4.

    Parameters
    ----------
    image:
        Input PIL image.
    scale:
        Integer upscale factor (e.g. ``2`` doubles each dimension).

    Returns
    -------
    PIL.Image.Image
        Upscaled image.

    Example::

        hires = upscale(img, scale=2)   # 640×480 → 1280×960
    """
    if scale < 1:
        raise ValueError("scale must be >= 1")
    w, h = image.size
    return image.resize((w * scale, h * scale), resample=Image.LANCZOS)


def convert_color_space(
    image: Image.Image,
    mode: str,
) -> Image.Image:
    """Convert *image* to a different PIL colour mode.

    Parameters
    ----------
    image:
        Input PIL image.
    mode:
        Target PIL mode, e.g. ``"L"`` (greyscale), ``"RGB"``, ``"RGBA"``,
        ``"CMYK"``, ``"HSV"``.

    Returns
    -------
    PIL.Image.Image
        Converted image.

    Example::

        grey = convert_color_space(img, "L")
        rgba = convert_color_space(img, "RGBA")
    """
    return image.convert(mode)


def add_noise(
    image: Image.Image,
    std: float = 15.0,
    seed: Optional[int] = None,
) -> Image.Image:
    """Add Gaussian noise to *image*.

    Parameters
    ----------
    image:
        Input PIL image.
    std:
        Standard deviation of the noise (0–255 range; 15 is subtle).
    seed:
        Optional random seed for reproducibility.

    Returns
    -------
    PIL.Image.Image
        Noisy image (pixel values clamped to [0, 255]).

    Example::

        noisy = add_noise(img, std=20)
    """
    rng = np.random.default_rng(seed)
    arr = np.array(image, dtype=np.float32)
    noise = rng.normal(0, std, arr.shape).astype(np.float32)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def denoise(
    image: Image.Image,
    size: int = 3,
) -> Image.Image:
    """Remove noise using a median filter.

    Parameters
    ----------
    image:
        Input PIL image.
    size:
        Median filter window size (must be odd, e.g. 3, 5).

    Returns
    -------
    PIL.Image.Image
        Denoised image.

    Example::

        clean = denoise(noisy_img, size=5)
    """
    return image.filter(ImageFilter.MedianFilter(size=size))
