"""Image processing sub-package."""

from smolvlm2_wrapper.image.processor import ImageProcessor
from smolvlm2_wrapper.image.manipulation import (
    resize,
    crop,
    rotate,
    flip,
    sharpen,
    blur,
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    apply_filter,
    upscale,
    convert_color_space,
    add_noise,
    denoise,
)
from smolvlm2_wrapper.image.mask import (
    create_mask,
    create_circular_mask,
    create_rect_mask,
    apply_mask,
    invert_mask,
    feather_mask,
    mask_from_color,
)
from smolvlm2_wrapper.image.inpaint import inpaint, outpaint, heal

__all__ = [
    "ImageProcessor",
    # manipulation
    "resize", "crop", "rotate", "flip",
    "sharpen", "blur",
    "adjust_brightness", "adjust_contrast", "adjust_saturation",
    "apply_filter", "upscale", "convert_color_space",
    "add_noise", "denoise",
    # masking
    "create_mask", "create_circular_mask", "create_rect_mask",
    "apply_mask", "invert_mask", "feather_mask", "mask_from_color",
    # inpainting / outpainting / healing
    "inpaint", "outpaint", "heal",
]
