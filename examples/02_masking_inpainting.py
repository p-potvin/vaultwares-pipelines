"""
02_masking_inpainting.py – Masks, inpainting, outpainting, and healing.

Run:
    python examples/02_masking_inpainting.py --image path/to/photo.jpg

This example shows:
  - Creating rectangular, circular, and colour-based masks
  - Feathering mask edges
  - Inpainting (fill a region from context)
  - Outpainting (extend the canvas)
  - Healing (remove an object / blemish)
"""

import argparse
from pathlib import Path

from PIL import Image

from ai_model.image.mask import (
    create_rect_mask, create_circular_mask, mask_from_color,
    feather_mask, apply_mask, invert_mask,
)
from ai_model.image.inpaint import inpaint, outpaint, heal
from ai_model.utils.io import load_image, save_image


def run(image_path: str, output_dir: str = "/tmp/smolvlm2_demo/masks") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    img = load_image(image_path)
    w, h = img.size

    # ── 1. rectangular mask ──────────────────────────────────────────────────
    cx, cy = w // 4, h // 4
    rect_mask = create_rect_mask(w, h, (cx, cy, cx * 3, cy * 3))
    rect_mask.save(out / "mask_rect.png")
    print("Saved   : mask_rect.png")

    # ── 2. circular mask ─────────────────────────────────────────────────────
    circ_mask = create_circular_mask(w, h, center=(w // 2, h // 2), radius=min(w, h) // 4)
    circ_mask.save(out / "mask_circle.png")
    print("Saved   : mask_circle.png")

    # ── 3. feathered mask ────────────────────────────────────────────────────
    soft_mask = feather_mask(rect_mask, radius=15)
    soft_mask.save(out / "mask_feathered.png")
    print("Saved   : mask_feathered.png")

    # ── 4. apply mask (image × mask) ─────────────────────────────────────────
    masked_img = apply_mask(img, circ_mask, background=(30, 30, 30))
    save_image(masked_img, out / "masked_result.jpg")
    print("Saved   : masked_result.jpg")

    # ── 5. inpainting ────────────────────────────────────────────────────────
    inpainted = inpaint(img, rect_mask)
    save_image(inpainted, out / "inpainted.jpg")
    print("Saved   : inpainted.jpg")

    # ── 6. outpainting (extend canvas by 10%) ────────────────────────────────
    pad = max(1, min(w, h) // 10)
    extended = outpaint(img, padding=(pad, pad, pad, pad))
    save_image(extended, out / "outpainted.jpg")
    print(f"Saved   : outpainted.jpg ({extended.size[0]}×{extended.size[1]})")

    # ── 7. healing (remove a circular region) ────────────────────────────────
    heal_mask = create_circular_mask(w, h, center=(w // 3, h // 3), radius=min(w, h) // 8)
    healed = heal(img, heal_mask, patch_size=16)
    save_image(healed, out / "healed.jpg")
    print("Saved   : healed.jpg")

    print(f"\nAll outputs written to {out}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="examples/sample.jpg")
    parser.add_argument("--out", default="/tmp/smolvlm2_demo/masks")
    args = parser.parse_args()
    run(args.image, args.out)
