"""
01_image_basics.py – Image loading, manipulation, and captioning.

Run:
    python examples/01_image_basics.py --image path/to/photo.jpg

This example shows:
  - Loading an image
  - Resize, sharpen, adjust brightness/contrast
  - Converting to greyscale
  - Upscaling
  - Saving results
  - Captioning with SmolVLM2 (optional – requires HuggingFace weights)
"""

import argparse
from pathlib import Path

from PIL import Image

# ── package imports ────────────────────────────────────────────────────────────
from ai_model.image.processor import ImageProcessor
from ai_model.image.manipulation import (
    resize, sharpen, blur, adjust_brightness,
    adjust_contrast, adjust_saturation, upscale,
)


def run(image_path: str, output_dir: str = "/tmp/smolvlm2_demo") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ── 1. load ──────────────────────────────────────────────────────────────
    proc = ImageProcessor()
    proc.load(image_path)
    original = proc.get_image()
    print(f"Loaded  : {image_path}  ({original.size[0]}×{original.size[1]})")

    # ── 2. resize ────────────────────────────────────────────────────────────
    proc.clone().resize(640, 480).save(out / "01_resized.jpg")
    print("Saved   : 01_resized.jpg")

    # ── 3. sharpen ───────────────────────────────────────────────────────────
    proc.clone().sharpen(radius=2, percent=200).save(out / "02_sharp.jpg")
    print("Saved   : 02_sharp.jpg")

    # ── 4. brightness + contrast ─────────────────────────────────────────────
    proc.clone() \
        .adjust_brightness(1.3) \
        .adjust_contrast(1.4) \
        .save(out / "03_vivid.jpg")
    print("Saved   : 03_vivid.jpg")

    # ── 5. greyscale ─────────────────────────────────────────────────────────
    proc.clone().adjust_saturation(0.0).save(out / "04_grey.jpg")
    print("Saved   : 04_grey.jpg")

    # ── 6. 2× upscale ────────────────────────────────────────────────────────
    proc.clone().upscale(2).save(out / "05_2x.jpg")
    print("Saved   : 05_2x.jpg")

    # ── 7. chainable pipeline ────────────────────────────────────────────────
    proc.clone() \
        .resize(512, 512) \
        .sharpen(percent=150) \
        .adjust_brightness(1.1) \
        .save(out / "06_pipeline.jpg")
    print("Saved   : 06_pipeline.jpg")

    # ── 8. (optional) model captioning ───────────────────────────────────────
    try:
        from ai_model import GenericTextModelWrapper
        model = GenericTextModelWrapper()
        proc2 = ImageProcessor(model=model)
        proc2.load(image_path)
        for style in ("brief", "detailed", "tags"):
            cap = proc2.caption(style=style)
            print(f"Caption ({style}): {cap}")
    except Exception as exc:
        print(f"[Model not loaded] {exc}")

    print(f"\nAll outputs written to {out}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="examples/sample.jpg", help="Input image path")
    parser.add_argument("--out", default="/tmp/smolvlm2_demo/images")
    args = parser.parse_args()
    run(args.image, args.out)
