"""Tests for image manipulation, masking, inpainting and the ImageProcessor."""

import numpy as np
import pytest
from PIL import Image

from ai_model.image.manipulation import (
    resize, crop, rotate, flip, sharpen, blur,
    adjust_brightness, adjust_contrast, adjust_saturation,
    apply_filter, upscale, convert_color_space, add_noise, denoise,
)
from ai_model.image.mask import (
    create_mask, create_rect_mask, create_circular_mask,
    apply_mask, invert_mask, feather_mask, mask_from_color,
)
from ai_model.image.inpaint import inpaint, outpaint, heal
from ai_model.image.processor import ImageProcessor


# ------------------------------------------------------------------ #
# helpers                                                             #
# ------------------------------------------------------------------ #

def _rgb(w=64, h=64):
    """Create a simple solid-colour test image."""
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[..., 0] = 100   # R
    arr[..., 1] = 150   # G
    arr[..., 2] = 200   # B
    return Image.fromarray(arr, mode="RGB")


# ------------------------------------------------------------------ #
# manipulation                                                        #
# ------------------------------------------------------------------ #

class TestManipulation:
    def test_resize(self):
        img = _rgb(64, 64)
        out = resize(img, 32, 32)
        assert out.size == (32, 32)

    def test_resize_upsample(self):
        img = _rgb(32, 32)
        out = resize(img, 128, 128)
        assert out.size == (128, 128)

    def test_crop(self):
        img = _rgb(64, 64)
        out = crop(img, 0, 0, 32, 32)
        assert out.size == (32, 32)

    def test_rotate(self):
        img = _rgb(64, 64)
        out = rotate(img, 90)
        assert isinstance(out, Image.Image)

    def test_flip_horizontal(self):
        img = _rgb(64, 64)
        out = flip(img, "horizontal")
        assert out.size == img.size

    def test_flip_vertical(self):
        img = _rgb(64, 64)
        out = flip(img, "vertical")
        assert out.size == img.size

    def test_flip_invalid(self):
        img = _rgb()
        with pytest.raises(ValueError):
            flip(img, "diagonal")

    def test_sharpen(self):
        img = _rgb()
        out = sharpen(img)
        assert out.size == img.size

    def test_blur(self):
        img = _rgb()
        out = blur(img, radius=3)
        assert out.size == img.size

    def test_adjust_brightness(self):
        img = _rgb()
        out = adjust_brightness(img, 1.5)
        assert out.size == img.size

    def test_adjust_contrast(self):
        img = _rgb()
        out = adjust_contrast(img, 1.3)
        assert out.size == img.size

    def test_adjust_saturation(self):
        img = _rgb()
        out = adjust_saturation(img, 0.0)
        arr = np.array(out)
        # all channels should be equal (greyscale)
        assert np.allclose(arr[:, :, 0], arr[:, :, 1], atol=2)

    def test_apply_filter_edge_enhance(self):
        img = _rgb()
        out = apply_filter(img, "edge_enhance")
        assert out.size == img.size

    def test_apply_filter_invalid(self):
        img = _rgb()
        with pytest.raises(ValueError):
            apply_filter(img, "does_not_exist")

    def test_upscale(self):
        img = _rgb(32, 32)
        out = upscale(img, scale=2)
        assert out.size == (64, 64)

    def test_upscale_invalid(self):
        img = _rgb()
        with pytest.raises(ValueError):
            upscale(img, scale=0)

    def test_convert_color_space_grey(self):
        img = _rgb()
        out = convert_color_space(img, "L")
        assert out.mode == "L"

    def test_add_noise(self):
        img = _rgb()
        out = add_noise(img, std=20, seed=42)
        assert out.size == img.size
        # output should differ from input
        assert not np.array_equal(np.array(img), np.array(out))

    def test_denoise(self):
        img = _rgb()
        noisy = add_noise(img, std=30, seed=0)
        out = denoise(noisy, size=3)
        assert out.size == img.size


# ------------------------------------------------------------------ #
# masking                                                             #
# ------------------------------------------------------------------ #

class TestMask:
    def test_create_mask_black(self):
        m = create_mask(64, 64, fill=0)
        assert m.mode == "L"
        assert np.array(m).max() == 0

    def test_create_mask_white(self):
        m = create_mask(64, 64, fill=255)
        assert np.array(m).min() == 255

    def test_create_rect_mask(self):
        m = create_rect_mask(64, 64, (10, 10, 50, 50))
        arr = np.array(m)
        assert arr[30, 30] == 255   # inside
        assert arr[0, 0] == 0       # outside

    def test_create_circular_mask(self):
        m = create_circular_mask(64, 64, center=(32, 32), radius=10)
        arr = np.array(m)
        assert arr[32, 32] == 255   # centre
        assert arr[0, 0] == 0       # far corner

    def test_apply_mask(self):
        img = _rgb()
        mask = create_mask(64, 64, fill=255)  # all white → keep all
        out = apply_mask(img, mask)
        assert np.allclose(np.array(out), np.array(img.convert("RGB")), atol=1)

    def test_invert_mask(self):
        m = create_mask(64, 64, fill=255)
        inv = invert_mask(m)
        assert np.array(inv).max() == 0

    def test_feather_mask(self):
        m = create_rect_mask(64, 64, (20, 20, 44, 44))
        feathered = feather_mask(m, radius=5)
        # edges should be softer (not strictly binary)
        arr = np.array(feathered)
        unique_vals = np.unique(arr)
        assert len(unique_vals) > 2

    def test_mask_from_color(self):
        img = _rgb()   # R=100, G=150, B=200
        m = mask_from_color(img, target_color=(100, 150, 200), tolerance=5)
        arr = np.array(m)
        assert arr.max() == 255  # at least some pixels selected


# ------------------------------------------------------------------ #
# inpainting                                                          #
# ------------------------------------------------------------------ #

class TestInpainting:
    def test_inpaint_shape(self):
        img = _rgb(64, 64)
        mask = create_rect_mask(64, 64, (20, 20, 44, 44))
        out = inpaint(img, mask)
        assert out.size == img.size

    def test_outpaint_expands(self):
        img = _rgb(32, 32)
        out = outpaint(img, padding=(10, 10, 10, 10))
        assert out.size == (52, 52)

    def test_outpaint_no_padding(self):
        img = _rgb(32, 32)
        out = outpaint(img, padding=(0, 0, 0, 0))
        assert out.size == img.size

    def test_heal_shape(self):
        img = _rgb(64, 64)
        mask = create_circular_mask(64, 64, center=(32, 32), radius=8)
        out = heal(img, mask, patch_size=8)
        assert out.size == img.size


# ------------------------------------------------------------------ #
# ImageProcessor                                                      #
# ------------------------------------------------------------------ #

class TestImageProcessor:
    def test_chain(self):
        proc = ImageProcessor()
        proc.set_image(_rgb(64, 64))
        proc.resize(32, 32).sharpen().blur(radius=1)
        assert proc.get_image().size == (32, 32)

    def test_no_image_raises(self):
        proc = ImageProcessor()
        with pytest.raises(RuntimeError):
            proc.get_image()

    def test_save_load(self, tmp_path):
        proc = ImageProcessor()
        proc.set_image(_rgb(64, 64))
        dest = tmp_path / "test.png"
        saved = proc.save(dest)
        assert saved.exists()
        # reload and compare
        proc2 = ImageProcessor()
        proc2.load(saved)
        assert proc2.get_image().size == (64, 64)

    def test_apply_mask(self):
        proc = ImageProcessor()
        proc.set_image(_rgb(64, 64))
        mask = create_mask(64, 64, fill=255)
        proc.apply_mask(mask)
        assert proc.get_image().size == (64, 64)

    def test_inpaint(self):
        proc = ImageProcessor()
        proc.set_image(_rgb(64, 64))
        mask = create_rect_mask(64, 64, (20, 20, 44, 44))
        proc.inpaint(mask)
        assert proc.get_image().size == (64, 64)

    def test_outpaint(self):
        proc = ImageProcessor()
        proc.set_image(_rgb(32, 32))
        proc.outpaint((10, 10, 10, 10))
        assert proc.get_image().size == (52, 52)

    def test_heal(self):
        proc = ImageProcessor()
        proc.set_image(_rgb(64, 64))
        mask = create_circular_mask(64, 64, center=(32, 32), radius=8)
        proc.heal(mask)
        assert proc.get_image().size == (64, 64)

    def test_caption_no_model_raises(self):
        proc = ImageProcessor()
        proc.set_image(_rgb())
        with pytest.raises(RuntimeError):
            proc.caption()

    def test_caption_with_model(self):
        class _MockModel:
            def caption(self, img, style="detailed"):
                return "a test image"
        proc = ImageProcessor(model=_MockModel())
        proc.set_image(_rgb())
        assert proc.caption() == "a test image"

    def test_clone_independence(self):
        proc = ImageProcessor()
        proc.set_image(_rgb(64, 64))
        clone = proc.clone()
        clone.resize(32, 32)
        assert proc.get_image().size == (64, 64)
        assert clone.get_image().size == (32, 32)
