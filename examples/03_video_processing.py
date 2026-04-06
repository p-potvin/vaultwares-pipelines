"""
03_video_processing.py – Trim, resize, apply effects, analyse with SmolVLM2.

Run:
    python examples/03_video_processing.py --video path/to/clip.mp4

This example shows:
  - Loading a video
  - Trimming to a sub-range
  - Resizing frames
  - Applying per-frame image effects
  - Stabilisation
  - Saving as GIF preview and MP4
  - Describing the video with SmolVLM2 (optional)
"""

import argparse
from pathlib import Path

from ai_model.video.processor import VideoProcessor
from ai_model.image.manipulation import sharpen, adjust_contrast


def run(video_path: str, output_dir: str = "/tmp/smolvlm2_demo/video") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    proc = VideoProcessor()
    proc.load(video_path)
    total = len(proc.get_frames())
    print(f"Loaded  : {video_path}  ({total} frames @ {proc._fps:.1f} fps)")

    # ── 1. sample 16 evenly-spaced frames ────────────────────────────────────
    preview_proc = proc.clone() if hasattr(proc, "clone") else VideoProcessor().set_frames(
        proc.get_frames(), proc._fps
    )
    # Simpler – work directly on proc by trimming first 120 frames
    proc.trim(0, min(120, total))
    print(f"Trimmed : {len(proc.get_frames())} frames")

    # ── 2. resize to 640×360 ─────────────────────────────────────────────────
    proc.resize(640, 360)
    print("Resized : 640×360")

    # ── 3. sharpen every frame ───────────────────────────────────────────────
    proc.apply_effect(lambda f: sharpen(f, percent=130))
    print("Applied : sharpen(130%)")

    # ── 4. save GIF preview (10 fps, 20 frames) ──────────────────────────────
    gif_proc = VideoProcessor().set_frames(proc.get_frames())
    gif_proc.sample(20)
    gif_path = gif_proc.save_gif(out / "preview.gif", fps=10)
    print(f"Saved   : {gif_path}")

    # ── 5. save edited video ─────────────────────────────────────────────────
    try:
        mp4_path = proc.save(out / "edited.mp4")
        print(f"Saved   : {mp4_path}")
    except Exception as exc:
        print(f"[MP4 save skipped] {exc}")

    # ── 6. (optional) model description ─────────────────────────────────────
    try:
        from ai_model import GenericTextModelWrapper
        model = GenericTextModelWrapper()
        desc_proc = VideoProcessor(model=model)
        desc_proc.set_frames(proc.get_frames())
        desc_proc.sample(8)
        description = desc_proc.describe()
        print(f"\nVideo description:\n{description}")
    except Exception as exc:
        print(f"[Model not loaded] {exc}")

    print(f"\nAll outputs written to {out}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Input video file")
    parser.add_argument("--out", default="/tmp/smolvlm2_demo/video")
    args = parser.parse_args()
    run(args.video, args.out)
