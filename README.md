# vaultwares-pipelines: Multi-Agent Workflow Platform


## Overview
A modular platform for text, image, and video generation/editing using AI agents, with workflow orchestration, compliance, and a Gradio-based GUI.

## Setup

1. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

2. Configure environment variables securely:
    - Copy `.env.example` to `.env` (local-only) and adjust values:
      ```env
      DB_URL=postgres://postgres:postgres@localhost:5432/vaultwares
      MODELS_DIR=D:/comfyui/resources/comfyui/models
      ```
    - Never commit secrets or sensitive paths to version control.

3. Set up your database:
    - Create a PostgreSQL database named `vaultwares` (or use your own connection string)
    - The script will auto-create the `ai_models` table if it does not exist.

4. Run the model discovery script:
    ```sh
    python scripts/discover_models.py
    ```
    ```
3. Run the Gradio GUI locally:
    ```bash
    python examples/workflow_gui_gradio.py
    ```
4. Open http://127.0.0.1:7860 in your browser.

### Frontend (React SPA)
1. Open a new terminal and navigate to `frontend/`:
    ```bash
    cd frontend
    ```
2. Install dependencies:
    ```bash
    npm install
    ```
3. Start the development server:
    ```bash
    npm run dev
    ```
4. Open the URL shown in the terminal (usually http://localhost:5173).

---

## Starting the API Server (FastAPI)

You can run the API server using the provided `api_server.py` file. This will start a FastAPI server exposing all workflow endpoints.

### 1. Install dependencies (if not already done):
```bash
pip install -r requirements.txt
```

### 2. (Recommended) Activate your virtual environment:
```bash
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3. Start the API server:
```bash
python api_server.py
```

- By default, the server will run on `http://127.0.0.1:8000`.
- By default, the server will run on `http://127.0.0.1:9001`.
- The OpenAPI/Swagger UI will be available at `http://127.0.0.1:9001/docs`.

**Note:** You can now run the API server directly with `python api_server.py` (no extra arguments needed) thanks to the new script entrypoint. For production or advanced usage, you can still use `uvicorn` directly:
```bash
pip install uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Homepage & Branding

When you visit `http://127.0.0.1:9001/` (or your configured API host/port), you'll see a branded Vaultwares Pipelines homepage with:
- A stylized Vaultwares graphic
- A link to the main frontend dashboard (placeholder URL)
- A link to register for an API key (placeholder URL)
- A link to the API docs (`/docs`)

You can customize the URLs for the dashboard and API key registration in `api_server.py` by editing the `FRONTEND_URL` and `API_KEY_REG_URL` variables.

---

## Module Documentation

### Backend Modules

- **api_server.py**: FastAPI server for workflow CRUD, backup/restore, and NIM VM integration. Endpoints: `/workflows`, `/workflows/export`, `/workflows/backup`, `/workflows/restore`, etc.

- **ai_model/**: Main Python package for all agent logic.
  - `agent_text.py`: Text agent (captioning, VQA, prompt engineering).
  - `agent_image.py`: Image agent (editing, masking, inpainting).
  - `agent_video.py`: Video agent (frame sampling, analysis, editing).
  - `agent_workflow.py`: Workflow orchestration and chaining.
  - `context_schema.py`: Shared context definitions for agents.
  - `compliance.py`: Compliance and validation hooks.
  - `central_error_logger.py`: Centralized error/event logging.
  - `workflow_export_agent.py`: Export workflows to ComfyUI/Diffusion formats.
  - `workflows/`: Built-in workflows (photo enhancement, inpainting, video analysis, etc.).
  - `core/`, `image/`, `video/`, `text/`, `utils/`: Core model wrappers, manipulation utilities, and processors.

- **vaultwares_agentciation/**: Social/coordination agents.
  - `extrovert_agent.py`: Team awareness, status, and socialization via Redis.
  - `lonely_manager.py`: Project alignment, TODO/roadmap monitoring, and nudges.
  - `base_agent.py`, `enums.py`, etc.: Agent base classes and enums.

- **examples/**: Example scripts and the main Gradio GUI (`workflow_gui_gradio.py`).

### Frontend Modules

- **frontend/src/App.jsx**: Main React SPA entry point. Renders sidebar, workflow list, modals, and all dashboard widgets.
- **frontend/src/WorkflowList.jsx**: Workflow list and actions (edit, delete, etc.).
- **frontend/src/Sidebar.jsx**: Category navigation sidebar.
- **frontend/src/Modal.jsx**: Modal dialog component for create/edit actions.
- **frontend/src/ImageTools.jsx**: Photo editing widget (crop, mask, resize, etc.).
- **frontend/src/ImageCaptioning.jsx**: Image captioning/tagging UI.
- **frontend/src/LoRATraining.jsx**: LoRA training workflow UI (dataset upload, params, training, export).
- **frontend/src/api.js**: API calls to backend for workflow CRUD.
- **frontend/src/store.js**: Redux store setup and state management.
- **frontend/src/validation.js**: Input validation utilities.
- **frontend/src/wireframes.md**: UI wireframes and layout sketches.

---

For more details, see in-line code comments and the [agent_manifest.md](agent_manifest.md) for planned features and architecture.
- `ai_model/agent_text.py` — Text agent logic
- `ai_model/agent_image.py` — Image agent logic
- `ai_model/agent_video.py` — Video agent logic
- `ai_model/agent_workflow.py` — Workflow orchestration
- `ai_model/context_schema.py` — Shared context definitions
- `ai_model/compliance.py` — Compliance hooks
- `ai_model/workflow_export_agent.py` — Export workflows to ComfyUI/Diffusion formats
- `ai_model/workflows/` — Built-in workflows
- `ai_model/core/`, `ai_model/image/`, `ai_model/video/`, `ai_model/text/`, `ai_model/utils/` — Core model wrappers, manipulation utilities, and processors
- `vaultwares_agentciation/extrovert_agent.py` — Team awareness, status, and socialization via Redis
- `vaultwares_agentciation/lonely_manager.py` — Project alignment, TODO/roadmap monitoring, and nudges
- `vaultwares_agentciation/base_agent.py` — Agent base classes
- `vaultwares_agentciation/enums.py`, etc. — enums, and shared utilities
- `examples/api_server.py` — FastAPI server
- `vaultwares_agentciation/central_error_logger.py` — Error/event logging with correlationId
- `examples/workflow_gui_gradio.py` — Quickstart Gradio GUI for workflow execution

## Example Usage (GUI)
- **Text-to-Image Workflow:**
  1. Select "Text-to-Image" workflow in the GUI
  2. Enter a prompt and steps
  3. Click "Run Workflow" to generate an image

## Troubleshooting
- If the GUI does not appear, open http://127.0.0.1:7860 manually
- For build issues, use the provided PowerShell script to clean and rebuild
- Check `gradio_error.log` for runtime errors

## Contributing
Pull requests and issues are welcome!


```
┌─────────────────────────────────────────────────────────────────┐
│                     ai_model                                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │   core/    │  │  image/    │  │  video/    │  │  text/   │  │
│  │ model base │  │manipulation│  │manipulation│  │prompts & │  │
│  │ SmolVLM2   │  │ inpaint    │  │ processor  │  │processor │  │
│  │ config     │  │ utils      │  │ processor  │  │          │  │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘  │
│  ┌──────────────────────────────────────────┐  ┌────────────┐   │
│  │         workflows/                       │  │  utils/    │   │
│  │  Workflow + Step base  │  5 examples     │  │ device, io │   │
│  └──────────────────────────────────────────┘  └────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Table of Contents

1. [Installation](#installation)
2. [Quick start](#quick-start)
3. [API reference](#api-reference)
   - [Core – model wrapper](#core--model-wrapper)
   - [Image manipulation](#image-manipulation)
   - [Masking](#masking)
   - [Inpainting, outpainting, healing](#inpainting-outpainting-healing)
   - [ImageProcessor (chainable)](#imageprocessor-chainable)
   - [Video manipulation](#video-manipulation)
   - [VideoProcessor (chainable)](#videoprocessor-chainable)
   - [Text & prompt utilities](#text--prompt-utilities)
   - [TextProcessor](#textprocessor)
   - [Workflow system](#workflow-system)
   - [Built-in workflows](#built-in-workflows)
   - [Device & I/O utilities](#device--io-utilities)
4. [Workflow documentation](#workflow-documentation)
5. [Extending to other models](#extending-to-other-models)
6. [Low-power device tips](#low-power-device-tips)
7. [Running the tests](#running-the-tests)
8. [Agent and Workflow Manager API](#agent-and-workflow-manager-api)
## Agent and Workflow Manager API

### ExtrovertAgent

`vaultwares_agentciation.extrovert_agent.ExtrovertAgent`

An agent that maintains live team awareness and socialization via Redis. Every user interaction triggers a heartbeat, status update, project re-evaluation, and peer acknowledgement. Includes:

- `start()` / `stop()` — lifecycle management
- `socialize()` — full team status broadcast and report
- `on_user_interaction()` — must be called before every user response
- `get_team_report()` — returns a human-readable team status block

#### Example
```python
from vaultwares_agentciation.extrovert_agent import ExtrovertAgent
agent = ExtrovertAgent("agent-1")
agent.start()
print(agent.socialize())
agent.stop()
```

### LonelyManager

`vaultwares_agentciation.lonely_manager.LonelyManager`

Extends ExtrovertAgent to enforce project alignment and monitor all agents. Features:

- Monitors heartbeats, triggers alerts for missed heartbeats
- Loads and previews TODO.md and roadmap.md
- Publishes project status and alignment nudges
- `get_project_status_report()` — full project/team status

#### Example
```python
from vaultwares_agentciation.lonely_manager import LonelyManager
manager = LonelyManager()
manager.start()
print(manager.get_project_status_report())
manager.stop()
```

### WorkflowExportAgent

`ai_model.workflow_export_agent.WorkflowExportAgent`

Exports Python-based workflows to ComfyUI/Diffusion formats, with validation and event publishing.

#### Example
```python
from ai_model.workflow_export_agent import WorkflowExportAgent
from ai_model.shared_context import SharedContext
agent = WorkflowExportAgent(SharedContext())
result = agent.export_to_comfyui({"foo": "bar"})
print(result)
```

---

## Installation

```bash
# 1. clone
git clone https://github.com/p-potvin/vaultwares-pipelines
cd vaultwares-pipelines

# 2. install (editable)
pip install -e ".[dev]"

# …or just the core runtime:
pip install -r requirements.txt
```

### Optional extras

| Extra | Command | Adds |
|---|---|---|
| Video support | `pip install opencv-python` | `VideoProcessor.load/save`, frame sampling, stabilisation |
| Audio muxing | requires `ffmpeg` on `$PATH` | `add_audio()` |
| Memory stats | `pip install psutil` | `DeviceManager.memory_info()` |

---

## Quick start

### Caption an image

```python
from ai_model import SmolVLM2Wrapper
from PIL import Image

model = SmolVLM2Wrapper()
caption = model.caption(Image.open("photo.jpg"), style="detailed")
print(caption)
```

### Chain image operations

```python
from ai_model.image.processor import ImageProcessor

result = (
    ImageProcessor()
    .load("photo.jpg")
    .resize(1024, 768)
    .sharpen(percent=150)
    .adjust_brightness(1.1)
    .adjust_contrast(1.2)
    .save("enhanced.jpg")
)
```

### Describe a video

```python
from ai_model.video.processor import SmolVLM2Wrapper, VideoProcessor

model = SmolVLM2Wrapper()
desc = (
    VideoProcessor(model=model)
    .load("clip.mp4")
    .sample(8)          # pick 8 evenly-spaced frames
    .describe()
)
print(desc)
```

### Generate a Stable Diffusion prompt

```python
from ai_model.core.smolvlm2 import SmolVLM2Wrapper
from ai_model.text.processor import TextProcessor
from PIL import Image

tp = TextProcessor(model=SmolVLM2Wrapper())
sd_prompt = tp.caption(Image.open("photo.jpg"), style="sd_prompt")
enhanced = tp.enhance_prompt(sd_prompt, image=Image.open("photo.jpg"))
print(enhanced)
```

---

## API reference

### Core – model wrapper

#### `ModelConfig`

```python
from ai_model.core.config import ModelConfig

cfg = ModelConfig(
    model_id="HuggingFaceTB/SmolVLM2-500M-Video-Instruct",
    device="auto",      # "auto" | "cuda" | "mps" | "cpu"
    dtype="float32",    # "float32" | "float16" | "bfloat16"
    max_new_tokens=256,
    do_sample=False,
    low_memory=False,   # enable CPU-offloading for <4 GB RAM devices
    cache_dir=None,     # override HuggingFace cache directory
)
```

#### `BaseModelWrapper`

Abstract base for any model.  Sub-class it to wrap your own model:

```python
from ai_model.core.model import BaseModelWrapper
from ai_model.core.config import ModelConfig

class MyModel(BaseModelWrapper):
    def _load_model(self):
        # load self._model and self._processor
        ...

    def generate(self, prompt, images=None, videos=None, **kwargs):
        # run inference, return str
        ...
```

#### `SmolVLM2Wrapper`

```python
from ai_model import SmolVLM2Wrapper

model = SmolVLM2Wrapper()            # default: SmolVLM2-500M on best device
model = SmolVLM2Wrapper(ModelConfig(device="cpu", low_memory=True))

# core
text = model.generate("What is this?", images=[img])
text = model.generate("Describe this clip.", videos=[frames])

# convenience
caption  = model.caption(img, style="brief|detailed|tags|cinematic|sd_prompt")
answer   = model.answer_question("How many people?", images=[img])
desc     = model.describe_video(frames, prompt="What is happening?")
enhanced = model.enhance_prompt("a sunset", image=img)
frames   = model.extract_video_frames("clip.mp4", max_frames=8)

# lifecycle
model.load()    # eager load (optional – auto-loads on first call)
model.unload()  # free GPU/RAM
```

---

### Image manipulation

All functions in `ai_model.image.manipulation` accept and return
`PIL.Image.Image` objects and never mutate inputs.

```python
from ai_model.image.manipulation import *

img = resize(img, width=640, height=480)
img = crop(img, left=0, top=0, right=200, bottom=200)
img = rotate(img, angle=90, expand=True)
img = flip(img, direction="horizontal")  # or "vertical"
img = sharpen(img, radius=2.0, percent=150, threshold=3)
img = adjust_brightness(img, factor=1.3)   # >1 = brighter
img = adjust_saturation(img, factor=0.0)  # 0 = greyscale, 1 = unchanged
img = apply_filter(img, name="edge_enhance")
     # names: edge_enhance, emboss, find_edges, smooth, detail, contour
img = upscale(img, scale=2)               # Lanczos ×2
img = convert_color_space(img, mode="L") # "L", "RGB", "RGBA", …
img = add_noise(img, std=15.0, seed=42)
img = denoise(img, size=3)               # median filter
```

---


```python
from ai_model.image.mask import *

mask = create_rect_mask(w, h, (left, top, right, bottom))
mask = create_circular_mask(w, h, center=(cx, cy), radius=r)
mask = mask_from_color(img, target_color=(R, G, B), tolerance=30)
mask = feather_mask(mask, radius=5.0)           # soften edges
mask = invert_mask(mask)                        # swap fore/background
img  = apply_mask(img, mask, background=(0,0,0))
```

**Mask convention:** white (255) = region of interest / fill target;
black (0) = background / leave unchanged.

---

### Inpainting, outpainting, healing

```python
from ai_model.image.inpaint import inpaint, outpaint, heal

# Fill the masked region using surrounding pixels
result = inpaint(image, mask)

# Extend the canvas (top, right, bottom, left) pixels each side
result = outpaint(image, padding=(0, 200, 0, 200))  # add 200px left/right

# Remove an object / blemish via patch matching
result = heal(image, mask, patch_size=16)
```

All three accept an optional `model=` argument; when a `SmolVLM2Wrapper`
(or any compatible wrapper) is supplied it will be used to provide
descriptive context that can be consumed by a downstream generative model.

---

### ImageProcessor (chainable)

```python

proc = ImageProcessor(model=SmolVLM2Wrapper())   # model is optional

result = (
    proc
    .resize(1024, 768)
    .adjust_brightness(1.1)
    .adjust_contrast(1.2)
    .adjust_saturation(0.9)
    .blur(radius=0.5)
    .denoise(size=3)
    .apply_filter("detail")
    .upscale(2)
    .flip("horizontal")
    .rotate(10)
    .convert("L")                 # greyscale
    .add_noise(std=5)
    .inpaint(mask)
    .outpaint((50, 50, 50, 50))
    .heal(blemish_mask)
    .save("output.jpg")           # returns pathlib.Path

# model-powered methods (require model=...)
caption  = proc.load("photo.jpg").caption(style="detailed")

from ai_model.video.manipulation import *
from ai_model.video.utils import sample_frames, frames_to_gif, add_audio

frames = sample_frames("clip.mp4", n=8)         # evenly sampled frames
frames = trim_frames(frames, start=10, end=50)
frames = resize_frames(frames, 640, 360)
frames = reverse_frames(frames)
frames = apply_frame_effect(frames, lambda f: sharpen(f, percent=130))
frames = add_frame_overlay(frames, logo_img, alpha=0.2, position=(10, 10))
frames = stabilize_frames(frames)               # requires opencv

frames_to_gif(frames, "preview.gif", fps=10)
add_audio("silent.mp4", "music.mp3", "final.mp4")  # requires ffmpeg
```

---

### VideoProcessor (chainable)

```python
from ai_model import SmolVLM2Wrapper, VideoProcessor

proc = VideoProcessor(model=SmolVLM2Wrapper())

(
    proc
    .load("clip.mp4")               # loads all frames + detects fps
    .sample(16)                     # keep 16 evenly-spaced frames
    .trim(start=0, end=90)          # keep frames 0–89
    .resize(640, 360)
    .reverse()
    .apply_effect(lambda f: sharpen(f))
    .add_overlay(logo, alpha=0.15)
    .stabilize()                    # requires opencv
    .save("edited.mp4")             # encode & write
)

# Export GIF preview
proc.load("clip.mp4").sample(20).save_gif("preview.gif", fps=10)

# Model-powered
desc     = proc.load("clip.mp4").sample(8).describe()
captions = proc.load("clip.mp4").sample(16).caption_frames(every_n=4)
```

---

### Text & prompt utilities

```python
from ai_model.text.prompts import (
    build_caption_prompt,
    build_vqa_prompt,
    build_enhancement_prompt,
    build_video_description_prompt,
    PromptTemplate,
    STYLE_PROMPTS,
)

# style names: "brief", "detailed", "tags", "cinematic", "sd_prompt"
prompt = build_caption_prompt("sd_prompt")
prompt = build_vqa_prompt("How many people are in the image?")
prompt = build_enhancement_prompt("a dog running")
prompt = build_video_description_prompt("scene")  # "action", "scene", "emotion", "summary"

# Custom template
t = PromptTemplate("Translate to {lang}: {text}", description="translation")
print(t.format(lang="French", text="Hello world"))
```

---

### TextProcessor

```python
from ai_model import SmolVLM2Wrapper
from ai_model.text.processor import TextProcessor

tp = TextProcessor(model=SmolVLM2Wrapper())

# captioning
cap = tp.caption(img, style="detailed")

# VQA
ans = tp.vqa("What is in the background?", images=[img])

# prompt enhancement
better = tp.enhance_prompt("a sunset over the ocean", image=img)

# video
desc = tp.describe_video(frames, focus="action")  # action, scene, emotion, summary

# batch
caps = tp.batch_caption([img1, img2, img3], style="brief")
ans  = tp.batch_vqa("Is there a person?", [img1, img2])

# list styles
TextProcessor.available_styles()
# → ['brief', 'detailed', 'tags', 'cinematic', 'sd_prompt']
```

---

### Workflow system

A `Workflow` is a sequence of named `Step` callables.  Each step receives
the context `dict`, must return an updated context `dict`, and must not
return `None`.

```python
from ai_model.workflows.base import Workflow, Step

wf = Workflow(name="my_pipeline")

wf.add_step(Step(
    name="load",
    fn=lambda ctx: {**ctx, "image": load_image(ctx["path"])},
    description="Load image from disk.",
))

wf.add_step(Step(
    name="sharpen",
    fn=lambda ctx: {**ctx, "image": sharpen(ctx["image"], percent=150)},
))

result = wf.run({"path": "photo.jpg"})
```

**Workflow composition:**

```python
combined = preprocess_workflow + analysis_workflow
result = combined.run(initial_ctx)
```

---

### Built-in workflows

| Class | Steps | Context keys |
|---|---|---|
| `PhotoEnhancementWorkflow` | load → resize → sharpen → brightness → contrast → save → (caption) | `image_path`, `output_path`, opt: `width`, `height`, `sharpen_percent`, `brightness`, `contrast` |
| `VideoAnalysisWorkflow` | sample → describe → caption_frames | `video_path`, opt: `n_frames`, `caption_style`, `description_focus` |
| `PromptGenerationWorkflow` | load → caption → enhance | `image_path`, opt: `caption_style` |
| `InpaintingWorkflow` | load → mask → inpaint → save → (caption) | `image_path`, `output_path`, `mask_box`, opt: `feather` |
| `VideoEditWorkflow` | load → trim → resize → effect → save → (describe) | `video_path`, `output_path`, opt: `trim_start`, `trim_end`, `width`, `height`, `effect`, `fps` |

```python
from ai_model.workflows.examples import PhotoEnhancementWorkflow

wf = PhotoEnhancementWorkflow(model=SmolVLM2Wrapper())
result = wf.run({
    "image_path": "photo.jpg",
    "output_path": "enhanced.jpg",
    "width": 1920,
    "height": 1080,
})
print(result["caption"])
```

---

### Device & I/O utilities

```python
from ai_model.utils.device import DeviceManager
from ai_model.utils.io import load_image, save_image, load_video, save_video

# device
dm = DeviceManager("auto")    # "auto" | "cuda" | "mps" | "cpu"
print(dm.resolve())            # "cuda", "mps", or "cpu"
print(DeviceManager.memory_info())

# image I/O
img = load_image("photo.jpg")  # str, pathlib.Path, or PIL.Image
save_image(img, "output/result.png")

# video I/O
frames = load_video("clip.mp4", max_frames=0)   # 0 = all frames
save_video(frames, "output/result.mp4", fps=30)
```

---

## Workflow documentation

### Workflow 1 – Photo enhancement pipeline

```
Input image
    │
    ▼
[resize]          fit to target canvas
    │
    ▼
[sharpen]         unsharp-mask to recover detail lost in resize
    │
    ▼
[brightness]      slight lift for screens/print
    │
    ▼
[contrast]        punch contrast to compensate for sharpening
    │
    ▼
[save]            write to disk
    │
    ▼
[caption]         (optional) SmolVLM2 → natural-language description
```

### Workflow 2 – Content-aware inpainting

```
Input image + region to remove
    │
    ▼
[create_rect_mask / create_circular_mask]
    │
    ▼
[feather_mask]    soften edges to prevent hard seams
    │
    ▼
[inpaint]         diffusion fill from surrounding pixels
    │              optionally guided by SmolVLM2 context description
    ▼
[save]
    │
    ▼
[caption]         verify result with SmolVLM2
```

### Workflow 3 – Stable Diffusion prompt generation

```
Reference image
    │
    ▼
[caption (sd_prompt style)]     describe in SD vocabulary
    │
    ▼
[enhance_prompt]                SmolVLM2 rewrites & expands
    │
    ▼
[result: rich SD prompt string] feed to SD / SDXL / FLUX
```

### Workflow 4 – Video analysis pipeline

```
Video file
    │
    ▼
[sample_frames(n=8)]            evenly sample key frames
    │
    ▼
[describe_video]                SmolVLM2 overall description
    │
    ▼
[caption_frames]                per-frame brief captions
    │
    ▼
[result dict]                   description + list of captions
```

### Workflow 5 – Video edit pipeline

```
Video file
    │
    ▼
[load]
    │
    ▼
[trim(start, end)]              remove unwanted segments
    │
    ▼
[resize(w, h)]                  downscale for delivery
    │
    ▼
[apply_effect(fn)]              per-frame transform (sharpen, denoise…)
    │
    ▼
[add_overlay(logo)]             branding / watermark
    │
    ▼
[stabilize]                     reduce camera shake
    │
    ▼
[save]                          encode MP4
    │
    ▼
[describe]                      (optional) SmolVLM2 QC pass
```

---

## Extending to other models

Sub-class `BaseModelWrapper` with two methods:

```python
from ai_model.core.model import BaseModelWrapper
from ai_model.core.config import ModelConfig

class LLaVAWrapper(BaseModelWrapper):
    DEFAULT_CONFIG = ModelConfig(model_id="llava-hf/llava-1.5-7b-hf")

    def _load_model(self):
        from transformers import LlavaProcessor, LlavaForConditionalGeneration
        import torch
        self._processor = LlavaProcessor.from_pretrained(self.config.model_id)
        self._model = LlavaForConditionalGeneration.from_pretrained(
            self.config.model_id, torch_dtype=torch.float16
        ).to(self.device)

    def generate(self, prompt, images=None, videos=None, **kwargs):
        if not self._loaded:
            self.load()
        inputs = self._processor(text=prompt, images=images, return_tensors="pt")
        inputs = inputs.to(self.device)
        out = self._model.generate(**inputs, **self.config.generation_kwargs())
        return self._processor.decode(out[0], skip_special_tokens=True)
```

Then pass it wherever `SmolVLM2Wrapper` is used:

```python
model = LLaVAWrapper()
proc  = ImageProcessor(model=model)
tp    = TextProcessor(model=model)
wf    = PhotoEnhancementWorkflow(model=model)
```

---

## Low-power device tips

```python
from ai_model import SmolVLM2Wrapper
from ai_model.core.config import ModelConfig

# Raspberry Pi / Jetson Nano / CPU-only server
model = SmolVLM2Wrapper(ModelConfig(
    device="cpu",
    dtype="float32",
    low_memory=True,      # enables low_cpu_mem_usage + offloading
    max_new_tokens=64,    # shorter generations = less compute
))

# Apple Silicon Mac
model = SmolVLM2Wrapper(ModelConfig(
    device="mps",
    dtype="float32",
))

# Reduce memory footprint further
model.unload()            # free weights when not in use
```

The **image and video manipulation functions** have no ML dependencies at
all and run efficiently on any hardware with NumPy + Pillow.

---

## Running the tests

```bash
# install test dependencies
pip install pytest numpy pillow

# run all tests
pytest tests/ -v

# run a single module
pytest tests/test_image.py -v
```

Tests cover:
- `test_core.py`      – ModelConfig, DeviceManager
- `test_image.py`     – all manipulation, mask, inpaint, and ImageProcessor operations
- `test_video.py`     – video manipulation, utils, VideoProcessor
- `test_text.py`      – PromptTemplate, prompt factories, TextProcessor
- `test_workflows.py` – Workflow base + all five built-in workflows + I/O utils

All tests run without downloading model weights.

---

## Project structure

```
ai_model/
├── __init__.py            top-level re-exports
├── core/
│   ├── config.py          ModelConfig dataclass
│   ├── model.py           BaseModelWrapper (abstract)
│   └── smolvlm2.py        SmolVLM2Wrapper (concrete)
├── image/
│   ├── manipulation.py    resize, crop, sharpen, blur, upscale …
│   ├── mask.py            create_mask, feather, apply, invert …
│   ├── inpaint.py         inpaint, outpaint, heal
│   └── processor.py       ImageProcessor (chainable)
├── video/
│   ├── manipulation.py    trim, resize, reverse, effect, overlay …
│   ├── utils.py           sample_frames, frames_to_gif, add_audio
│   └── processor.py       VideoProcessor (chainable)
├── text/
│   ├── prompts.py         PromptTemplate + factory functions
│   └── processor.py       TextProcessor
├── workflows/
│   ├── base.py            Workflow + Step
│   └── examples.py        5 ready-to-use workflows
└── utils/
    ├── device.py           DeviceManager
    └── io.py               load/save image & video
tests/
    test_core.py
    test_image.py
    test_video.py
    test_text.py
    test_workflows.py
examples/
    01_image_basics.py
    02_masking_inpainting.py
    03_video_processing.py
    04_prompt_generation.py
    05_workflows.py
