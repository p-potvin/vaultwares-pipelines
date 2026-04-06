"""
04_prompt_generation.py – Caption images and generate/enhance prompts for SD/SDXL.

Run:
    python examples/04_prompt_generation.py --image path/to/photo.jpg

This example shows:
  - Multi-style image captioning (brief, detailed, tags, cinematic, sd_prompt)
  - Prompt enhancement for Stable Diffusion
  - Visual question answering (VQA)
  - Using TextProcessor for batch operations

Requires SmolVLM2 weights to be downloadable from HuggingFace.
"""

import argparse

from ai_model import GenericTextModelWrapper
from ai_model.text.processor import TextProcessor
from ai_model.utils.io import load_image


def run(image_path: str) -> None:
    print("Loading model …")
    model = GenericTextModelWrapper()
    tp = TextProcessor(model=model)
    img = load_image(image_path)

    # ── 1. captioning in multiple styles ─────────────────────────────────────
    print("\n── Captions ─────────────────────────────────────────────────────")
    for style in TextProcessor.available_styles():
        cap = tp.caption(img, style=style)
        print(f"  [{style:12s}] {cap[:120]}")

    # ── 2. VQA ───────────────────────────────────────────────────────────────
    print("\n── Visual Q&A ───────────────────────────────────────────────────")
    for q in [
        "What is the main subject of this image?",
        "What colours dominate this image?",
        "Is there any text visible in this image?",
    ]:
        answer = tp.vqa(q, images=[img])
        print(f"  Q: {q}")
        print(f"  A: {answer}\n")

    # ── 3. prompt enhancement ─────────────────────────────────────────────────
    print("── Prompt Enhancement ───────────────────────────────────────────")
    base_prompts = [
        "a portrait photo",
        "a landscape at sunset",
        "a city street at night",
    ]
    for bp in base_prompts:
        enhanced = tp.enhance_prompt(bp, image=img)
        print(f"  Base : {bp}")
        print(f"  Enhanced: {enhanced[:200]}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Input image path")
    args = parser.parse_args()
    run(args.image)
