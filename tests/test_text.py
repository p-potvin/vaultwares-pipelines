"""Tests for text prompts and the TextProcessor."""

import pytest
from PIL import Image
import numpy as np

from ai_model.text.prompts import (
    build_caption_prompt,
    build_vqa_prompt,
    build_enhancement_prompt,
    build_video_description_prompt,
    PromptTemplate,
    STYLE_PROMPTS,
)
from ai_model.text.processor import TextProcessor


# ------------------------------------------------------------------ #
# helpers                                                             #
# ------------------------------------------------------------------ #

def _img():
    arr = np.zeros((32, 32, 3), dtype=np.uint8)
    return Image.fromarray(arr, "RGB")


class _MockModel:
    """Minimal stub that records calls."""
    def __init__(self, response="mock response"):
        self._response = response
        self.calls = []

    def generate(self, prompt, images=None, videos=None, **kw):
        self.calls.append({"prompt": prompt, "images": images, "videos": videos})
        return self._response

    def caption(self, img, style="detailed"):
        return f"caption:{style}"

    def enhance_prompt(self, prompt, image=None):
        return f"enhanced:{prompt}"


# ------------------------------------------------------------------ #
# PromptTemplate                                                      #
# ------------------------------------------------------------------ #

class TestPromptTemplate:
    def test_format(self):
        t = PromptTemplate(template="Hello {name}!", description="greeting")
        assert t.format(name="world") == "Hello world!"

    def test_str(self):
        t = PromptTemplate(template="test {x}")
        assert str(t) == "test {x}"


# ------------------------------------------------------------------ #
# prompt factories                                                    #
# ------------------------------------------------------------------ #

class TestPromptFactories:
    def test_build_caption_prompt_all_styles(self):
        for style in STYLE_PROMPTS:
            p = build_caption_prompt(style)
            assert isinstance(p, str) and len(p) > 0

    def test_build_caption_prompt_invalid(self):
        with pytest.raises(ValueError):
            build_caption_prompt("nonexistent_style")

    def test_build_vqa_prompt(self):
        p = build_vqa_prompt("How many cats?")
        assert "How many cats?" in p

    def test_build_enhancement_prompt(self):
        p = build_enhancement_prompt("a sunset")
        assert "a sunset" in p

    def test_build_video_description_prompt(self):
        for focus in ("action", "scene", "emotion", "summary"):
            p = build_video_description_prompt(focus)
            assert isinstance(p, str) and len(p) > 0

    def test_build_video_description_prompt_invalid(self):
        with pytest.raises(ValueError):
            build_video_description_prompt("bad_focus")


# ------------------------------------------------------------------ #
# TextProcessor                                                       #
# ------------------------------------------------------------------ #

class TestTextProcessor:
    def test_caption(self):
        model = _MockModel()
        tp = TextProcessor(model=model)
        result = tp.caption(_img(), style="brief")
        assert len(model.calls) == 1
        assert result == "mock response"

    def test_vqa(self):
        model = _MockModel()
        tp = TextProcessor(model=model)
        result = tp.vqa("What is this?", images=[_img()])
        assert "What is this?" in model.calls[0]["prompt"]
        assert result == "mock response"

    def test_enhance_prompt(self):
        model = _MockModel()
        tp = TextProcessor(model=model)
        result = tp.enhance_prompt("a dog")
        assert "a dog" in model.calls[0]["prompt"]

    def test_describe_video(self):
        model = _MockModel()
        tp = TextProcessor(model=model)
        frames = [_img() for _ in range(4)]
        result = tp.describe_video(frames, focus="summary")
        assert model.calls[0]["videos"] == [frames]

    def test_batch_caption(self):
        model = _MockModel("cap")
        tp = TextProcessor(model=model)
        imgs = [_img(), _img(), _img()]
        caps = tp.batch_caption(imgs, style="brief")
        assert caps == ["cap", "cap", "cap"]

    def test_batch_vqa(self):
        model = _MockModel("yes")
        tp = TextProcessor(model=model)
        answers = tp.batch_vqa("Is there a cat?", [_img(), _img()])
        assert answers == ["yes", "yes"]

    def test_no_model_raises(self):
        tp = TextProcessor()
        with pytest.raises(RuntimeError):
            tp.caption(_img())
        with pytest.raises(RuntimeError):
            tp.vqa("?")
        with pytest.raises(RuntimeError):
            tp.enhance_prompt("test")
        with pytest.raises(RuntimeError):
            tp.describe_video([_img()])

    def test_available_styles(self):
        styles = TextProcessor.available_styles()
        assert "brief" in styles
        assert "detailed" in styles
        assert "tags" in styles
