"""Tests for the Workflow base class and pre-built example workflows."""

import pytest
from PIL import Image
import numpy as np

from ai_model.workflows.base import Workflow, Step
from ai_model.workflows.examples import (
    PhotoEnhancementWorkflow,
    InpaintingWorkflow,
    PromptGenerationWorkflow,
)


def _img(w=64, h=64):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[..., 0] = 100
    return Image.fromarray(arr, "RGB")


class _MockModel:
    def caption(self, img, style="detailed"):
        return f"cap:{style}"

    def enhance_prompt(self, prompt, image=None):
        return f"enhanced:{prompt}"

    def generate(self, prompt, images=None, videos=None, **kw):
        return "generated"


# ------------------------------------------------------------------ #
# Workflow base                                                        #
# ------------------------------------------------------------------ #

class TestWorkflowBase:
    def test_empty_workflow(self):
        wf = Workflow("test")
        result = wf.run({"x": 1})
        assert result == {"x": 1}

    def test_single_step(self):
        wf = Workflow("test")
        wf.add_step(Step("add", lambda ctx: {**ctx, "y": ctx["x"] + 1}))
        result = wf.run({"x": 5})
        assert result["y"] == 6

    def test_multiple_steps(self):
        wf = Workflow("test")
        wf.add_step(Step("double", lambda ctx: {**ctx, "v": ctx["v"] * 2}))
        wf.add_step(Step("add_one", lambda ctx: {**ctx, "v": ctx["v"] + 1}))
        result = wf.run({"v": 3})
        assert result["v"] == 7  # 3*2+1

    def test_step_returning_none_raises(self):
        wf = Workflow("test")
        wf.add_step(Step("bad", lambda ctx: None))
        with pytest.raises(RuntimeError, match="returned None"):
            wf.run({})

    def test_add_operator(self):
        wf1 = Workflow("a")
        wf1.add_step(Step("s1", lambda ctx: {**ctx, "s1": True}))
        wf2 = Workflow("b")
        wf2.add_step(Step("s2", lambda ctx: {**ctx, "s2": True}))
        combined = wf1 + wf2
        result = combined.run({})
        assert result["s1"] is True
        assert result["s2"] is True

    def test_repr(self):
        wf = Workflow("mywf")
        wf.add_step(Step("step1", lambda ctx: ctx))
        assert "mywf" in repr(wf)
        assert "step1" in repr(wf)

    def test_prepend_step(self):
        wf = Workflow("test")
        wf.add_step(Step("second", lambda ctx: {**ctx, "order": ctx.get("order", []) + ["second"]}))
        wf.prepend_step(Step("first", lambda ctx: {**ctx, "order": ctx.get("order", []) + ["first"]}))
        result = wf.run({})
        assert result["order"] == ["first", "second"]


# ------------------------------------------------------------------ #
# PhotoEnhancementWorkflow                                            #
# ------------------------------------------------------------------ #

class TestPhotoEnhancementWorkflow:
    def test_runs_without_model(self, tmp_path):
        src = tmp_path / "in.png"
        out = tmp_path / "out.png"
        _img().save(src)
        wf = PhotoEnhancementWorkflow()
        result = wf.run({
            "image_path": str(src),
            "output_path": str(out),
            "width": 32,
            "height": 32,
        })
        assert out.exists()
        assert result["image"].size == (32, 32)

    def test_runs_with_model(self, tmp_path):
        src = tmp_path / "in.png"
        out = tmp_path / "out.png"
        _img().save(src)
        model = _MockModel()
        wf = PhotoEnhancementWorkflow(model=model)
        result = wf.run({
            "image_path": str(src),
            "output_path": str(out),
            "width": 32,
            "height": 32,
        })
        assert "caption" in result
        assert result["caption"].startswith("cap:")


# ------------------------------------------------------------------ #
# InpaintingWorkflow                                                  #
# ------------------------------------------------------------------ #

class TestInpaintingWorkflow:
    def test_runs(self, tmp_path):
        src = tmp_path / "in.png"
        out = tmp_path / "out.png"
        _img(64, 64).save(src)
        wf = InpaintingWorkflow()
        result = wf.run({
            "image_path": str(src),
            "output_path": str(out),
            "mask_box": (10, 10, 54, 54),
        })
        assert out.exists()
        assert result["image"].size == (64, 64)


# ------------------------------------------------------------------ #
# PromptGenerationWorkflow                                            #
# ------------------------------------------------------------------ #

class TestPromptGenerationWorkflow:
    def test_runs_with_model(self, tmp_path):
        src = tmp_path / "in.png"
        _img().save(src)
        model = _MockModel()
        wf = PromptGenerationWorkflow(model=model)
        result = wf.run({"image_path": str(src)})
        assert "sd_prompt" in result


# ------------------------------------------------------------------ #
# io utilities                                                        #
# ------------------------------------------------------------------ #

class TestIOUtils:
    def test_save_load_image(self, tmp_path):
        from ai_model.utils.io import save_image, load_image
        img = _img()
        dest = tmp_path / "test.png"
        save_image(img, dest)
        loaded = load_image(dest)
        assert loaded.size == img.size

    def test_load_image_missing(self, tmp_path):
        from ai_model.utils.io import load_image
        with pytest.raises(FileNotFoundError):
            load_image(tmp_path / "does_not_exist.png")

    def test_load_pil_passthrough(self):
        from ai_model.utils.io import load_image
        img = _img()
        loaded = load_image(img)
        assert loaded.mode == "RGB"
