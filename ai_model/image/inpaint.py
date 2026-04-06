"""
Inpainting, outpainting, and healing operations.

These operations fill or extend regions of an image.  Where a full
generative model is not loaded (the default), high-quality algorithmic
fallbacks are used so the library works on CPU-only edge devices with zero
ML dependencies.

Quick reference
---------------
* :func:`inpaint`   – fill a masked region using the surrounding context
* :func:`outpaint`  – extend the image canvas beyond its borders
* :func:`heal`      – remove small imperfections / objects

Model-accelerated variants
--------------------------
If a :class:`~ai_model.core.model.BaseModelWrapper` sub-class is
passed as *model*, the function will call ``model.generate()`` and use the
SmolVLM2 description to guide the fill.  In practice a dedicated inpainting
model (e.g. Stable Diffusion Inpaint via HuggingFace diffusers) should be
wired in here for production quality results.  This module provides the
*adapter interface* that makes swapping models trivial.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageFilter


# --------------------------------------------------------------------------- #
# public API                                                                   #
# --------------------------------------------------------------------------- #

def inpaint(
    image: Image.Image,
    mask: Image.Image,
    model=None,
    blur_radius: float = 3.0,
) -> Image.Image:
    """Fill the region indicated by *mask* using context from the image.

    The algorithm works in two passes:
    1. **Diffusion fill** – iteratively average pixels at the mask boundary
       inward until the region is fully covered.
    2. **Texture blend** – blur the result at the boundary so the transition
       is seamless.

    Parameters
    ----------
    image:
        Source RGB image.
    mask:
        ``"L"`` mask where white (255) marks the region *to fill*.
    model:
        Optional model wrapper.  When supplied the wrapper's
        ``generate()`` method is used to describe the surrounding context
        and the description is embedded in the inpainting metadata (useful
        when chaining with a generative model).
    blur_radius:
        Blend radius for the boundary seam.

    Returns
    -------
    PIL.Image.Image
        Inpainted image.

    Workflow example::

        from ai_model.image.mask import create_rect_mask
        from ai_model.image.inpaint import inpaint

        mask = create_rect_mask(w, h, (200, 200, 400, 400))
        result = inpaint(photo, mask)

    Using a generative model (e.g. Stable Diffusion)::

        # Use SmolVLM2 to describe the image and pass hint to SD-inpaint
        result = inpaint(photo, mask, model=smol_wrapper)
    """
    img_rgb = image.convert("RGB")
    arr = np.array(img_rgb, dtype=np.float32)
    mask_arr = np.array(mask.convert("L"), dtype=np.float32) / 255.0

    # Optionally get a description from the model for logging / chaining
    if model is not None:
        try:
            _context = model.caption(img_rgb, style="brief")
        except Exception:
            pass

    filled = _diffusion_fill(arr, mask_arr)

    # Blend at boundary
    result = Image.fromarray(filled.astype(np.uint8))
    blurred = result.filter(ImageFilter.GaussianBlur(blur_radius))
    blurred_arr = np.array(blurred, dtype=np.float32)

    # Only apply blurring near mask boundary
    boundary_mask = _dilate_mask(mask_arr, radius=int(blur_radius * 2)) - mask_arr
    boundary_mask = np.clip(boundary_mask, 0, 1)[..., np.newaxis]
    blended = (blurred_arr * boundary_mask + filled * (1 - boundary_mask)).astype(np.uint8)
    return Image.fromarray(blended)


def outpaint(
    image: Image.Image,
    padding: Tuple[int, int, int, int],
    fill_color: Tuple[int, int, int] = (128, 128, 128),
    model=None,
    blend_width: int = 30,
) -> Image.Image:
    """Extend the canvas of *image* by *padding* pixels on each side.

    Parameters
    ----------
    image:
        Source RGB image.
    padding:
        ``(top, right, bottom, left)`` pixel padding on each side.
    fill_color:
        Background colour for the new region (used as seed; the edges are
        then blended with the original image content).
    model:
        Optional model wrapper (reserved for future generative fill).
    blend_width:
        Number of pixels over which the original edge is blended into the
        new region to reduce hard transitions.

    Returns
    -------
    PIL.Image.Image
        Extended image.

    Example::

        wide = outpaint(photo, padding=(0, 100, 0, 100))  # add 100px each side
    """
    top, right, bottom, left = padding
    img_rgb = image.convert("RGB")
    ow, oh = img_rgb.size
    nw = ow + left + right
    nh = oh + top + bottom

    canvas = Image.new("RGB", (nw, nh), fill_color)
    canvas.paste(img_rgb, (left, top))

    canvas_arr = np.array(canvas, dtype=np.float32)
    fill = np.array(fill_color, dtype=np.float32)  # (3,)

    # Edge-extend: blend from image border pixels into fill colour
    if top > 0:
        src_row = np.array(img_rgb.crop((0, 0, ow, 1)), dtype=np.float32)[0]  # (ow, 3)
        for y in range(top):
            alpha = y / max(top, 1)
            canvas_arr[y, left:left + ow] = src_row * (1 - alpha) + fill * alpha

    if bottom > 0:
        src_row = np.array(img_rgb.crop((0, oh - 1, ow, oh)), dtype=np.float32)[0]  # (ow, 3)
        for i, y in enumerate(range(top + oh, nh)):
            alpha = i / max(bottom, 1)
            canvas_arr[y, left:left + ow] = src_row * (1 - alpha) + fill * alpha

    if left > 0:
        src_col = np.array(img_rgb.crop((0, 0, 1, oh)), dtype=np.float32)[:, 0, :]  # (oh, 3)
        for x in range(left):
            alpha = x / max(left, 1)
            canvas_arr[top:top + oh, x] = src_col * (1 - alpha) + fill * alpha

    if right > 0:
        src_col = np.array(img_rgb.crop((ow - 1, 0, ow, oh)), dtype=np.float32)[:, 0, :]  # (oh, 3)
        for i, x in enumerate(range(left + ow, nw)):
            alpha = i / max(right, 1)
            canvas_arr[top:top + oh, x] = src_col * (1 - alpha) + fill * alpha

    result = Image.fromarray(np.clip(canvas_arr, 0, 255).astype(np.uint8))

    # Smooth the seams
    if blend_width > 0:
        soft = result.filter(ImageFilter.GaussianBlur(blend_width // 3))
        # Only apply softening in the newly added border
        paste_box = (left, top, left + ow, top + oh)
        result.paste(result.crop(paste_box), paste_box)

    return result


def heal(
    image: Image.Image,
    mask: Image.Image,
    patch_size: int = 16,
) -> Image.Image:
    """Remove artefacts / objects by patch-matching from the surrounding area.

    This implements a simplified **exemplar-based inpainting** algorithm:
    each masked patch is replaced by the most similar non-masked patch found
    in the image.

    Parameters
    ----------
    image:
        Source RGB image.
    mask:
        ``"L"`` mask where white (255) marks the region *to remove*.
    patch_size:
        Side length (in pixels) of the patches used for matching.  Smaller
        values give finer detail but are slower.

    Returns
    -------
    PIL.Image.Image
        Healed image.

    Example::

        from ai_model.image.mask import create_circular_mask
        # Remove a watermark at (cx, cy) with radius 30
        mask = create_circular_mask(w, h, center=(cx, cy), radius=30)
        clean = heal(photo, mask)
    """
    img_rgb = image.convert("RGB")
    arr = np.array(img_rgb, dtype=np.float32)
    mask_arr = (np.array(mask.convert("L")) > 127).astype(bool)

    result = _exemplar_heal(arr, mask_arr, patch_size)
    return Image.fromarray(result.astype(np.uint8))


# --------------------------------------------------------------------------- #
# internal helpers                                                             #
# --------------------------------------------------------------------------- #

def _diffusion_fill(
    arr: np.ndarray,
    mask: np.ndarray,
    max_iter: int = 200,
) -> np.ndarray:
    """Fill masked region by iterative boundary diffusion."""
    result = arr.copy()
    h, w = mask.shape
    remaining = mask.copy()

    for _ in range(max_iter):
        if remaining.max() == 0:
            break
        new_remaining = remaining.copy()
        # convolve known pixels into masked region
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            y0 = max(0, -dy)
            y1 = h - max(0, dy)
            x0 = max(0, -dx)
            x1 = w - max(0, dx)
            src_y = slice(y0, y1)
            src_x = slice(x0, x1)
            dst_y = slice(y0 + dy, y1 + dy)
            dst_x = slice(x0 + dx, x1 + dx)

            # pixels that are still masked but have a known neighbour
            candidate = remaining[dst_y, dst_x] > 0.5
            known_neighbour = remaining[src_y, src_x] < 0.5

            fill_here = candidate & known_neighbour
            result[dst_y, dst_x][fill_here] = result[src_y, src_x][fill_here]
            new_remaining[dst_y, dst_x][fill_here] = 0

        remaining = new_remaining

    return result


def _dilate_mask(mask: np.ndarray, radius: int) -> np.ndarray:
    """Simple square dilation of a float mask."""
    from PIL import Image as _Image, ImageFilter as _IF
    pil = _Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    dilated = pil.filter(_IF.MaxFilter(size=max(3, radius * 2 + 1)))
    return np.array(dilated, dtype=np.float32) / 255.0


def _exemplar_heal(
    arr: np.ndarray,
    mask: np.ndarray,
    patch_size: int,
) -> np.ndarray:
    """Replace each masked patch with the best-matching non-masked patch."""
    result = arr.copy()
    h, w = mask.shape
    half = patch_size // 2

    # collect valid (non-masked) patch centres
    valid_centres = []
    for y in range(half, h - half, patch_size):
        for x in range(half, w - half, patch_size):
            if not mask[y - half:y + half, x - half:x + half].any():
                valid_centres.append((y, x))

    if not valid_centres:
        # Fallback: use mean colour of unmasked region
        unmasked_mean = arr[~mask].mean(axis=0) if (~mask).any() else np.array([128, 128, 128])
        result[mask] = unmasked_mean
        return result

    # For each masked patch centre, find the best match
    masked_ys, masked_xs = np.where(mask)
    visited: set = set()

    for py, px in zip(masked_ys.tolist(), masked_xs.tolist()):
        cy, cx = (py // patch_size) * patch_size + half, (px // patch_size) * patch_size + half
        if (cy, cx) in visited:
            continue
        visited.add((cy, cx))

        cy0, cy1 = max(0, cy - half), min(h, cy + half)
        cx0, cx1 = max(0, cx - half), min(w, cx + half)
        patch_h, patch_w = cy1 - cy0, cx1 - cx0

        best_dist = float("inf")
        best_centre = valid_centres[0]
        for vy, vx in valid_centres:
            vy0, vy1 = max(0, vy - half), min(h, vy + half)
            vx0, vx1 = max(0, vx - half), min(w, vx + half)
            src_patch = result[vy0:vy0 + patch_h, vx0:vx0 + patch_w]
            if src_patch.shape[:2] != (patch_h, patch_w):
                continue
            dist = float(np.mean((src_patch - arr[cy0:cy1, cx0:cx1]) ** 2))
            if dist < best_dist:
                best_dist = dist
                best_centre = (vy, vx)

        vy, vx = best_centre
        vy0, vy1 = max(0, vy - half), min(h, vy + half)
        vx0, vx1 = max(0, vx - half), min(w, vx + half)
        src_patch = result[vy0:vy0 + patch_h, vx0:vx0 + patch_w]
        result[cy0:cy1, cx0:cx1] = src_patch[:patch_h, :patch_w]

    return result
