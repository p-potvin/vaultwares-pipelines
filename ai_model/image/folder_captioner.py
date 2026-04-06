"""
Module: folder_captioner.py
--------------------------
Batch-caption a folder of images for LoRA training.
Supports SD1.5, SDXL (via 'sd_prompt'), and natural language styles.
Outputs: .txt (per image), .json, and .csv with all captions.

Usage:
    python folder_captioner.py --input <folder> --model <model_type> [--output <folder>]
    model_type: sd15 | sdxl | natural

Example:
    python folder_captioner.py --input ./images --model sd15 --output ./captions
"""
import argparse
import json
import csv
from pathlib import Path
from PIL import Image
from smolvlm2_wrapper import SmolVLM2Wrapper
from smolvlm2_wrapper.text.processor import TextProcessor
from smolvlm2_wrapper.utils.io import load_image

def get_style(model_type):
    if model_type.lower() in ["sd15", "sdxl"]:
        return "sd_prompt"
    return "detailed"

def caption_folder(input_dir, output_dir, model_type):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = SmolVLM2Wrapper()
    tp = TextProcessor(model=model)
    style = get_style(model_type)
    captions = {}
    for img_path in input_dir.glob("*.jpg"):
        img = load_image(img_path)
        cap = tp.caption(img, style=style)
        captions[img_path.name] = cap
        # Write .txt per image
        with open(output_dir / f"{img_path.stem}.txt", "w", encoding="utf-8") as f:
            f.write(cap)
    # Write all captions to JSON
    with open(output_dir / "captions.json", "w", encoding="utf-8") as f:
        json.dump(captions, f, indent=2, ensure_ascii=False)
    # Write all captions to CSV
    with open(output_dir / "captions.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "caption"])
        for fname, cap in captions.items():
            writer.writerow([fname, cap])
    print(f"Captioned {len(captions)} images. Outputs in {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Batch-caption images for LoRA training.")
    parser.add_argument("--input", required=True, help="Input folder of images")
    parser.add_argument("--output", default="./captions", help="Output folder")
    parser.add_argument("--model", required=True, choices=["sd15", "sdxl", "natural"], help="Captioning style/model")
    args = parser.parse_args()
    caption_folder(args.input, args.output, args.model)

if __name__ == "__main__":
    main()
