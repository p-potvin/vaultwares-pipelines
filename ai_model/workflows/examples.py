"""
Ready-to-use workflow examples.

Each class is a :class:`~ai_model.workflows.base.Workflow` sub-class
pre-configured for a specific use-case.  They are both useful stand-alone
and serve as templates for custom pipelines.

Available workflows
-------------------
* :class:`PhotoEnhancementWorkflow`  – resize → sharpen → adjust enhancement + caption
* :class:`VideoAnalysisWorkflow`     – sample frames → describe + per-frame captions
* :class:`PromptGenerationWorkflow`  – caption image → enhance prompt for SD/SDXL
* :class:`InpaintingWorkflow`        – mask region → inpaint → caption
* :class:`VideoEditWorkflow`         – load → trim → resize → effect → save

Usage::

    from ai_model import GenericTextModelWrapper
    from ai_model.workflows.examples import PhotoEnhancementWorkflow

    model = GenericTextModelWrapper()
    wf = PhotoEnhancementWorkflow(model=model)
    result = wf.run({
        "image_path": "photo.jpg",
        "output_path": "enhanced.jpg",
        "width": 1024,
        "height": 768,
    })
    print(result["caption"])
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ai_model.workflows.base import Workflow, Step


# --------------------------------------------------------------------------- #
# helpers                                                                      #
# --------------------------------------------------------------------------- #

def _load_image(ctx: Dict[str, Any]) -> Dict[str, Any]:
    from ai_model.utils.io import load_image
    return {**ctx, "image": load_image(ctx["image_path"])}


def _save_image(ctx: Dict[str, Any]) -> Dict[str, Any]:
    from ai_model.utils.io import save_image
    save_image(ctx["image"], ctx["output_path"])
    return ctx


def _save_video(ctx: Dict[str, Any]) -> Dict[str, Any]:
    from ai_model.utils.io import save_video
    save_video(ctx["frames"], ctx["output_path"], fps=ctx.get("fps", 24))
    return ctx


# --------------------------------------------------------------------------- #
# PhotoEnhancementWorkflow                                                     #
# --------------------------------------------------------------------------- #

class PhotoEnhancementWorkflow(Workflow):
    """Resize → sharpen → brightness/contrast boost → (optionally) caption.

    Context keys
    ------------
    Required:
        * ``image_path`` (str) – input image file path
        * ``output_path`` (str) – where to save the result

    Optional:
        * ``width`` (int, default 1024) – target width
        * ``height`` (int, default 768) – target height
        * ``sharpen_percent`` (int, default 150)
        * ``brightness`` (float, default 1.1)
        * ``contrast`` (float, default 1.2)

    Produces:
        * ``image`` – processed PIL image
        * ``caption`` – model caption (only if model was supplied)

    Example::

        from ai_model import GenericTextModelWrapper
        from ai_model.workflows.examples import PhotoEnhancementWorkflow

        wf = PhotoEnhancementWorkflow(model=GenericTextModelWrapper())
        result = wf.run({"image_path": "photo.jpg", "output_path": "out.jpg"})
        print(result["caption"])
    """

    def __init__(self, model=None) -> None:
        super().__init__(name="PhotoEnhancement")
        self._model = model

        self.add_step(Step("load", _load_image, "Load image from disk."))
        self.add_step(Step(
            "resize",
            lambda ctx: {**ctx, "image": __import__(
                "ai_model.image.manipulation", fromlist=["resize"]
            ).resize(ctx["image"], ctx.get("width", 1024), ctx.get("height", 768))},
            "Resize to target dimensions.",
        ))
        self.add_step(Step(
            "sharpen",
            lambda ctx: {**ctx, "image": __import__(
                "ai_model.image.manipulation", fromlist=["sharpen"]
            ).sharpen(ctx["image"], percent=ctx.get("sharpen_percent", 150))},
            "Unsharp-mask sharpening.",
        ))
        self.add_step(Step(
            "brightness",
            lambda ctx: {**ctx, "image": __import__(
                "ai_model.image.manipulation", fromlist=["adjust_brightness"]
            ).adjust_brightness(ctx["image"], ctx.get("brightness", 1.1))},
            "Adjust brightness.",
        ))
        self.add_step(Step(
            "contrast",
            lambda ctx: {**ctx, "image": __import__(
                "ai_model.image.manipulation", fromlist=["adjust_contrast"]
            ).adjust_contrast(ctx["image"], ctx.get("contrast", 1.2))},
            "Adjust contrast.",
        ))
        self.add_step(Step("save", _save_image, "Save processed image."))

        if model is not None:
            self.add_step(Step(
                "caption",
                lambda ctx: {**ctx, "caption": model.caption(ctx["image"], style="detailed")},
                "Generate caption with SmolVLM2.",
            ))


# --------------------------------------------------------------------------- #
# VideoAnalysisWorkflow                                                        #
# --------------------------------------------------------------------------- #

class VideoAnalysisWorkflow(Workflow):
    """Sample frames → overall description + per-frame captions.

    Context keys
    ------------
    Required:
        * ``video_path`` (str)
        * ``model`` – model wrapper OR passed to constructor

    Optional:
        * ``n_frames`` (int, default 8) – number of frames to sample
        * ``caption_style`` (str, default ``"brief"``)
        * ``description_focus`` (str, default ``"action"``)

    Produces:
        * ``frames`` – sampled PIL frames
        * ``description`` – overall video description
        * ``captions`` – list of per-frame captions

    Example::

        from ai_model import GenericTextModelWrapper
        from ai_model.workflows.examples import VideoAnalysisWorkflow

        wf = VideoAnalysisWorkflow(model=GenericTextModelWrapper())
        result = wf.run({"video_path": "clip.mp4"})
        print(result["description"])
    """

    def __init__(self, model=None) -> None:
        super().__init__(name="VideoAnalysis")
        self._model = model

        def _sample(ctx: Dict[str, Any]) -> Dict[str, Any]:
            from ai_model.video.utils import sample_frames
            return {**ctx, "frames": sample_frames(ctx["video_path"], n=ctx.get("n_frames", 8))}

        self.add_step(Step("sample_frames", _sample, "Sample N frames from the video."))

        def _describe(ctx: Dict[str, Any]) -> Dict[str, Any]:
            m = ctx.get("model") or model
            if m is None:
                return {**ctx, "description": ""}
            from ai_model.text.prompts import build_video_description_prompt
            prompt = build_video_description_prompt(ctx.get("description_focus", "action"))
            return {**ctx, "description": m.generate(prompt, videos=[ctx["frames"]])}

        self.add_step(Step("describe", _describe, "Generate overall video description."))

        def _caption_frames(ctx: Dict[str, Any]) -> Dict[str, Any]:
            m = ctx.get("model") or model
            if m is None:
                return {**ctx, "captions": []}
            style = ctx.get("caption_style", "brief")
            return {**ctx, "captions": [m.caption(f, style=style) for f in ctx["frames"]]}

        self.add_step(Step("caption_frames", _caption_frames, "Caption each sampled frame."))


# --------------------------------------------------------------------------- #
# PromptGenerationWorkflow                                                     #
# --------------------------------------------------------------------------- #

class PromptGenerationWorkflow(Workflow):
    """Caption image → enhance the caption into a Stable Diffusion prompt.

    Context keys
    ------------
    Required:
        * ``image_path`` (str)

    Optional:
        * ``caption_style`` (str, default ``"sd_prompt"``)

    Produces:
        * ``image``       – loaded PIL image
        * ``raw_caption`` – initial caption
        * ``sd_prompt``   – enhanced Stable Diffusion prompt

    Example::

        from ai_model import GenericTextModelWrapper
        from ai_model.workflows.examples import PromptGenerationWorkflow

        wf = PromptGenerationWorkflow(model=GenericTextModelWrapper())
        result = wf.run({"image_path": "photo.jpg"})
        print(result["sd_prompt"])
    """

    def __init__(self, model=None) -> None:
        super().__init__(name="PromptGeneration")
        self._model = model

        self.add_step(Step("load", _load_image, "Load image."))

        def _caption(ctx: Dict[str, Any]) -> Dict[str, Any]:
            m = ctx.get("model") or model
            if m is None:
                return {**ctx, "raw_caption": ""}
            style = ctx.get("caption_style", "sd_prompt")
            return {**ctx, "raw_caption": m.caption(ctx["image"], style=style)}

        self.add_step(Step("caption", _caption, "Generate initial caption."))

        def _enhance(ctx: Dict[str, Any]) -> Dict[str, Any]:
            m = ctx.get("model") or model
            if m is None:
                return {**ctx, "sd_prompt": ctx.get("raw_caption", "")}
            return {**ctx, "sd_prompt": m.enhance_prompt(
                ctx["raw_caption"], image=ctx["image"]
            )}

        self.add_step(Step("enhance", _enhance, "Enhance caption into SD prompt."))


# --------------------------------------------------------------------------- #
# InpaintingWorkflow                                                           #
# --------------------------------------------------------------------------- #

class InpaintingWorkflow(Workflow):
    """Create mask → inpaint → caption result.

    Context keys
    ------------
    Required:
        * ``image_path`` (str)
        * ``output_path`` (str)
        * ``mask_box`` (tuple) – ``(left, top, right, bottom)`` rect to inpaint

    Optional:
        * ``feather`` (float, default 3.0) – mask feather radius

    Produces:
        * ``image``  – inpainted PIL image
        * ``mask``   – the mask used
        * ``caption`` – caption of the result (if model supplied)

    Example::

        from ai_model.workflows.examples import InpaintingWorkflow

        wf = InpaintingWorkflow()
        result = wf.run({
            "image_path": "photo.jpg",
            "output_path": "inpainted.jpg",
            "mask_box": (200, 200, 400, 400),
        })
    """

    def __init__(self, model=None) -> None:
        super().__init__(name="Inpainting")
        self._model = model

        self.add_step(Step("load", _load_image, "Load image."))

        def _make_mask(ctx: Dict[str, Any]) -> Dict[str, Any]:
            from ai_model.image.mask import create_rect_mask, feather_mask
            img = ctx["image"]
            w, h = img.size
            raw_mask = create_rect_mask(w, h, ctx["mask_box"])
            m = feather_mask(raw_mask, radius=ctx.get("feather", 3.0))
            return {**ctx, "mask": m}

        self.add_step(Step("create_mask", _make_mask, "Create rectangular feathered mask."))

        def _inpaint(ctx: Dict[str, Any]) -> Dict[str, Any]:
            from ai_model.image.inpaint import inpaint
            return {**ctx, "image": inpaint(ctx["image"], ctx["mask"], model=model)}

        self.add_step(Step("inpaint", _inpaint, "Fill masked region."))
        self.add_step(Step("save", _save_image, "Save result."))

        if model is not None:
            self.add_step(Step(
                "caption",
                lambda ctx: {**ctx, "caption": model.caption(ctx["image"])},
                "Caption the inpainted result.",
            ))


# --------------------------------------------------------------------------- #
# VideoEditWorkflow                                                            #
# --------------------------------------------------------------------------- #

class VideoEditWorkflow(Workflow):
    """Load video → trim → resize → apply effect → save.

    Context keys
    ------------
    Required:
        * ``video_path`` (str)
        * ``output_path`` (str)

    Optional:
        * ``trim_start`` (int, default 0)
        * ``trim_end``   (int | None, default None)
        * ``width``      (int | None) – resize width
        * ``height``     (int | None) – resize height
        * ``effect``     (callable | None) – ``Image → Image`` function
        * ``fps``        (float, default 24)

    Produces:
        * ``frames`` – processed frames
        * ``description`` (if model supplied)

    Example::

        from ai_model.image.manipulation import sharpen
        from ai_model.workflows.examples import VideoEditWorkflow

        wf = VideoEditWorkflow()
        wf.run({
            "video_path": "clip.mp4",
            "output_path": "edited.mp4",
            "trim_start": 0,
            "trim_end": 90,
            "width": 640,
            "height": 360,
            "effect": lambda f: sharpen(f, percent=120),
        })
    """

    def __init__(self, model=None) -> None:
        super().__init__(name="VideoEdit")
        self._model = model

        def _load_video(ctx: Dict[str, Any]) -> Dict[str, Any]:
            from ai_model.utils.io import load_video
            import cv2
            cap = cv2.VideoCapture(str(ctx["video_path"]))
            fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            cap.release()
            frames = load_video(ctx["video_path"])
            return {**ctx, "frames": frames, "fps": ctx.get("fps", fps)}

        self.add_step(Step("load", _load_video, "Load video frames."))

        def _trim(ctx: Dict[str, Any]) -> Dict[str, Any]:
            from ai_model.video.manipulation import trim_frames
            return {**ctx, "frames": trim_frames(
                ctx["frames"],
                start=ctx.get("trim_start", 0),
                end=ctx.get("trim_end"),
            )}

        self.add_step(Step("trim", _trim, "Trim frame range."))

        def _resize(ctx: Dict[str, Any]) -> Dict[str, Any]:
            w, h = ctx.get("width"), ctx.get("height")
            if w and h:
                from ai_model.video.manipulation import resize_frames
                return {**ctx, "frames": resize_frames(ctx["frames"], w, h)}
            return ctx

        self.add_step(Step("resize", _resize, "Resize frames if width/height provided."))

        def _effect(ctx: Dict[str, Any]) -> Dict[str, Any]:
            fn = ctx.get("effect")
            if fn is not None:
                from ai_model.video.manipulation import apply_frame_effect
                return {**ctx, "frames": apply_frame_effect(ctx["frames"], fn)}
            return ctx

        self.add_step(Step("effect", _effect, "Apply per-frame image effect."))
        self.add_step(Step("save", _save_video, "Encode and save video."))

        if model is not None:
            def _describe(ctx: Dict[str, Any]) -> Dict[str, Any]:
                from ai_model.video.utils import sample_frames as _sf
                sampled = ctx["frames"][::max(1, len(ctx["frames"]) // 8)][:8]
                return {**ctx, "description": model.describe_video(sampled)}
            self.add_step(Step("describe", _describe, "Describe processed video."))
