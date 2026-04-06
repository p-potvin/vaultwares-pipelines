"""
05_workflows.py – End-to-end pipeline examples using the Workflow API.

Run:
    python examples/05_workflows.py --image path/to/photo.jpg

Demonstrates:
  - PhotoEnhancementWorkflow  (resize → sharpen → brightness/contrast → caption)
  - InpaintingWorkflow        (mask → inpaint → save)
  - PromptGenerationWorkflow  (caption → enhance for SD)
  - Custom Workflow built from first principles
"""

import argparse
from pathlib import Path

from ai_model.workflows.examples import (
    PhotoEnhancementWorkflow,
    InpaintingWorkflow,
    PromptGenerationWorkflow,
)
from ai_model.workflows.base import Workflow, Step
from ai_model.image.manipulation import sharpen, adjust_contrast
from ai_model.utils.io import load_image, save_image


def run(image_path: str, output_dir: str = "/tmp/smolvlm2_demo/workflows") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ── 1. PhotoEnhancementWorkflow (no model) ────────────────────────────────
    print("── PhotoEnhancementWorkflow (no model) ──────────────────────────")
    wf = PhotoEnhancementWorkflow()
    result = wf.run({
        "image_path": image_path,
        "output_path": str(out / "enhanced.jpg"),
        "width": 1024,
        "height": 768,
        "sharpen_percent": 160,
        "brightness": 1.1,
        "contrast": 1.2,
    })
    print(f"  Output : {out / 'enhanced.jpg'}")

    # ── 2. InpaintingWorkflow ─────────────────────────────────────────────────
    print("\n── InpaintingWorkflow ───────────────────────────────────────────")
    img = load_image(image_path)
    w, h = img.size
    cx, cy = w // 4, h // 4
    wf2 = InpaintingWorkflow()
    result2 = wf2.run({
        "image_path": image_path,
        "output_path": str(out / "inpainted.jpg"),
        "mask_box": (cx, cy, cx * 3, cy * 3),
        "feather": 10.0,
    })
    print(f"  Output : {out / 'inpainted.jpg'}")

    # ── 3. PromptGenerationWorkflow (with model if available) ─────────────────
    print("\n── PromptGenerationWorkflow ─────────────────────────────────────")
    try:
        from ai_model import GenericTextModelWrapper
        model = GenericTextModelWrapper()
        wf3 = PromptGenerationWorkflow(model=model)
        result3 = wf3.run({"image_path": image_path})
        print(f"  Raw caption : {result3.get('raw_caption', '')[:120]}")
        print(f"  SD prompt   : {result3.get('sd_prompt', '')[:200]}")
    except Exception as exc:
        print(f"  [Skipped – model not available]: {exc}")

    # ── 4. Custom Workflow: denoise → upscale → save ──────────────────────────
    print("\n── Custom Workflow: denoise → upscale → save ────────────────────")
    custom_wf = Workflow("denoise_upscale")
    custom_wf.add_step(Step(
        "load",
        lambda ctx: {**ctx, "image": load_image(ctx["image_path"])},
    ))
    custom_wf.add_step(Step(
        "denoise",
        lambda ctx: {
            **ctx,
            "image": __import__("ai_model.image.manipulation", fromlist=["denoise"])
                     .denoise(ctx["image"], size=3),
        },
    ))
    custom_wf.add_step(Step(
        "upscale",
        lambda ctx: {
            **ctx,
            "image": __import__("ai_model.image.manipulation", fromlist=["upscale"])
                     .upscale(ctx["image"], scale=2),
        },
    ))
    custom_wf.add_step(Step(
        "save",
        lambda ctx: {**ctx, "_saved": save_image(ctx["image"], ctx["output_path"])},
    ))

    res4 = custom_wf.run({
        "image_path": image_path,
        "output_path": str(out / "denoised_2x.jpg"),
    })
    print(f"  Output : {res4['_saved']}")
    print(f"\nAll outputs written to {out}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Input image path")
    parser.add_argument("--out", default="/tmp/smolvlm2_demo/workflows")
    args = parser.parse_args()
    run(args.image, args.out)
