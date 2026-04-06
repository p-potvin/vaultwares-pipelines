"""Tests for video processing utilities and the VideoProcessor."""

import numpy as np
import pytest
from PIL import Image

from ai_model.video.manipulation import (
    trim_frames, resize_frames, reverse_frames,
    apply_frame_effect, add_frame_overlay,
)
from ai_model.video.utils import frames_to_gif
from ai_model.video.processor import VideoProcessor


# ------------------------------------------------------------------ #
# helpers                                                             #
# ------------------------------------------------------------------ #

def _frame(w=64, h=64, color=(100, 150, 200)):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    return Image.fromarray(arr, mode="RGB")


def _frames(n=10):
    return [_frame() for _ in range(n)]


# ------------------------------------------------------------------ #
# manipulation                                                        #
# ------------------------------------------------------------------ #

class TestVideoManipulation:
    def test_trim_start_end(self):
        f = _frames(10)
        assert trim_frames(f, 2, 7) == f[2:7]

    def test_trim_open_end(self):
        f = _frames(10)
        assert trim_frames(f, 3) == f[3:]

    def test_resize_frames(self):
        f = _frames(4)
        out = resize_frames(f, 32, 32)
        assert all(fr.size == (32, 32) for fr in out)

    def test_reverse_frames(self):
        f = _frames(5)
        rev = reverse_frames(f)
        assert rev == f[::-1]

    def test_apply_frame_effect(self):
        from ai_model.image.manipulation import blur
        f = _frames(4)
        out = apply_frame_effect(f, lambda fr: blur(fr, radius=1))
        assert len(out) == 4
        assert all(isinstance(fr, Image.Image) for fr in out)

    def test_add_frame_overlay(self):
        f = _frames(3)
        overlay = _frame(16, 16, color=(255, 0, 0))
        out = add_frame_overlay(f, overlay, alpha=0.5, position=(0, 0))
        assert len(out) == 3
        assert all(isinstance(fr, Image.Image) for fr in out)


# ------------------------------------------------------------------ #
# utils                                                               #
# ------------------------------------------------------------------ #

class TestVideoUtils:
    def test_frames_to_gif(self, tmp_path):
        f = _frames(5)
        dest = tmp_path / "test.gif"
        result = frames_to_gif(f, dest, fps=5)
        assert result.exists()

    def test_frames_to_gif_empty_raises(self, tmp_path):
        with pytest.raises(ValueError):
            frames_to_gif([], tmp_path / "bad.gif")


# ------------------------------------------------------------------ #
# VideoProcessor                                                      #
# ------------------------------------------------------------------ #

class TestVideoProcessor:
    def test_set_get_frames(self):
        f = _frames(8)
        proc = VideoProcessor()
        proc.set_frames(f)
        assert proc.get_frames() == f

    def test_trim(self):
        proc = VideoProcessor()
        proc.set_frames(_frames(10))
        proc.trim(2, 7)
        assert len(proc.get_frames()) == 5

    def test_resize(self):
        proc = VideoProcessor()
        proc.set_frames(_frames(4))
        proc.resize(32, 32)
        assert all(fr.size == (32, 32) for fr in proc.get_frames())

    def test_reverse(self):
        f = _frames(5)
        proc = VideoProcessor()
        proc.set_frames(f)
        proc.reverse()
        assert proc.get_frames() == f[::-1]

    def test_apply_effect(self):
        from ai_model.image.manipulation import sharpen
        proc = VideoProcessor()
        proc.set_frames(_frames(3))
        proc.apply_effect(lambda fr: sharpen(fr, percent=150))
        assert len(proc.get_frames()) == 3

    def test_sample(self):
        proc = VideoProcessor()
        proc.set_frames(_frames(100))
        proc.sample(8)
        assert len(proc.get_frames()) == 8

    def test_save_gif(self, tmp_path):
        proc = VideoProcessor()
        proc.set_frames(_frames(5))
        dest = tmp_path / "out.gif"
        result = proc.save_gif(dest, fps=5)
        assert result.exists()

    def test_describe_no_model_raises(self):
        proc = VideoProcessor()
        proc.set_frames(_frames(4))
        with pytest.raises(RuntimeError):
            proc.describe()

    def test_describe_with_model(self):
        class _MockModel:
            def describe_video(self, frames, prompt=""):
                return "a test video"
        proc = VideoProcessor(model=_MockModel())
        proc.set_frames(_frames(4))
        result = proc.describe()
        assert result == "a test video"

    def test_caption_frames_with_model(self):
        class _MockModel:
            def caption(self, img, style="brief"):
                return "frame"
        proc = VideoProcessor(model=_MockModel())
        proc.set_frames(_frames(4))
        captions = proc.caption_frames(every_n=2)
        assert captions == ["frame", "frame"]

    def test_chain(self, tmp_path):
        proc = VideoProcessor()
        proc.set_frames(_frames(10))
        proc.trim(0, 6).resize(32, 32).reverse()
        assert len(proc.get_frames()) == 6
        assert proc.get_frames()[0].size == (32, 32)
