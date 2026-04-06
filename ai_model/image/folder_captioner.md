# Folder Captioner for LoRA Training

Batch-caption a folder of images for LoRA training. Supports SD1.5, SDXL (via 'sd_prompt'), and natural language styles. Outputs: .txt (per image), .json, and .csv with all captions.

## Usage

```bash
python -m ai_model.image.folder_captioner --input <folder> --model <model_type> [--output <folder>]
```
- `model_type`: sd15 | sdxl | natural

Example:
```bash
python -m ai_model.image.folder_captioner --input ./images --model sd15 --output ./captions
```

- Outputs a .txt file per image, plus captions.json and captions.csv in the output folder.
- Uses the correct prompt style for SD1.5/SDXL ("sd_prompt") or natural language ("detailed").
