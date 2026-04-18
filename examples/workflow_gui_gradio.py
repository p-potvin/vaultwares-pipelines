"""
Gradio GUI for multi-step text-to-image/image-editing workflows with real-time resource monitoring.
- Workflow selection, parameter input, execution, output/log display
- Live CPU/GPU/RAM/Temp/time usage panel

Required: pip install gradio psutil GPUtil pynvml matplotlib diffusers torch pillow
"""

import gradio as gr
import psutil
import GPUtil
import pynvml
import time
import matplotlib.pyplot as plt
from threading import Thread
from queue import Queue
from PIL import Image
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_model.cosmos_3d_env_workflow import cosmos_3d_env_run


# LRU Model Cache for all workflows
from collections import OrderedDict


# Size-based LRU Model Cache for all workflows (ComfyUI-style)
import torch

def estimate_model_size(model):
    # Try to estimate model size in bytes
    total = 0
    # PyTorch nn.Module
    if hasattr(model, 'parameters'):
        for p in model.parameters():
            if hasattr(p, 'element_size') and hasattr(p, 'nelement'):
                total += p.element_size() * p.nelement()
    # Diffusers pipeline (has .components)
    elif hasattr(model, 'components'):
        for comp in model.components:
            total += estimate_model_size(comp)
    # torch.Tensor
    elif isinstance(model, torch.Tensor):
        total += model.element_size() * model.nelement()
    # Fallback: try .nbytes
    elif hasattr(model, 'nbytes'):
        total += model.nbytes
    # Fallback: user can override or supply size
    return total if total > 0 else 100*1024*1024  # Default: 100MB


# --- Configurable ModelCache and SessionTracker ---
class ModelCache:
    def __init__(self, max_bytes=10*1024*1024*1024, device=None, offload_after_run=True):
        self.cache = OrderedDict()
        self.sizes = OrderedDict()
        self.max_bytes = max_bytes
        self.total_bytes = 0
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.offload_after_run = offload_after_run

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            self.sizes.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key, model, size_bytes=None):
        if key in self.cache:
            self.cache.move_to_end(key)
            self.sizes.move_to_end(key)
            return
        size = size_bytes if size_bytes is not None else estimate_model_size(model)
        # Evict until under limit
        while self.total_bytes + size > self.max_bytes and self.cache:
            old_key, old_model = self.cache.popitem(last=False)
            old_size = self.sizes.pop(old_key, 0)
            self.total_bytes -= old_size
            self._offload_model(old_model)
            del old_model
        self.cache[key] = model
        self.sizes[key] = size
        self.total_bytes += size

    def offload(self, key):
        model = self.cache.get(key)
        if model is not None:
            self._offload_model(model)

    def reload(self, key):
        model = self.cache.get(key)
        if model is not None and self.device:
            try:
                model.to(self.device)
            except Exception:
                pass

    def _offload_model(self, model):
        if hasattr(model, 'to'):
            try:
                model.to('cpu')
            except Exception:
                pass
        if hasattr(model, 'unload'):
            try:
                model.unload()
            except Exception:
                pass
        # Free VRAM if using CUDA
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass

    def clear(self):
        for model in self.cache.values():
            self._offload_model(model)
            del model
        self.cache.clear()
        self.sizes.clear()
        self.total_bytes = 0

    def update_config(self, max_bytes=None, device=None, offload_after_run=None):
        if max_bytes is not None:
            self.max_bytes = max_bytes
        if device is not None:
            self.device = device
        if offload_after_run is not None:
            self.offload_after_run = offload_after_run

# Global config for GUI binding
CACHE_CONFIG = {
    "max_vram_gb": 10,
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "offload_after_run": True
}

MODEL_CACHE = ModelCache(
    max_bytes=CACHE_CONFIG["max_vram_gb"]*1024*1024*1024,
    device=CACHE_CONFIG["device"],
    offload_after_run=CACHE_CONFIG["offload_after_run"]
)

# --- SessionTracker for last-use offloading ---
class SessionTracker:
    def __init__(self):
        self.model_calls = []  # List of (key, step_idx)
        self.last_use = {}     # key -> last step idx

    def record(self, key, step_idx):
        self.model_calls.append((key, step_idx))
        self.last_use[key] = step_idx

    def get_last_use(self, key):
        return self.last_use.get(key, -1)

    def clear(self):
        self.model_calls.clear()
        self.last_use.clear()

# --- Helper to update cache config from GUI ---
def update_cache_config(max_vram_gb=None, device=None, offload_after_run=None):
    if max_vram_gb is not None:
        CACHE_CONFIG["max_vram_gb"] = max_vram_gb
    if device is not None:
        CACHE_CONFIG["device"] = device
    if offload_after_run is not None:
        CACHE_CONFIG["offload_after_run"] = offload_after_run
    MODEL_CACHE.update_config(
        max_bytes=CACHE_CONFIG["max_vram_gb"]*1024*1024*1024,
        device=CACHE_CONFIG["device"],
        offload_after_run=CACHE_CONFIG["offload_after_run"]
    )

# Initialize NVML for GPU temp
try:
    pynvml.nvmlInit()
except Exception:
    pass



def run_sd_pipeline(params, log):
    import torch
    from diffusers import StableDiffusionPipeline
    from PIL import Image
    import os
    model_type = params.get("model_type", "checkpoints")
    model_file = params.get("model_file", "")
    prompt = params.get("prompt", "A futuristic cityscape at sunset with flying cars")
    steps = int(params.get("steps", 30))
    base = "D:/comfyui/resources/comfyui/models/"
    model_path = os.path.join(base, model_type, model_file)
    session = SessionTracker()
    if not os.path.isfile(model_path):
        log(f"Model file not found: {model_path}")
        return Image.new("RGB", (512, 512), color="red"), f"Model file not found: {model_path}"
    try:
        cache_key = ("sd", model_path)
        step_idx = 0
        pipe = MODEL_CACHE.get(cache_key)
        session.record(cache_key, step_idx)
        if pipe is not None:
            log(f"Using cached model: {model_path}")
        else:
            log(f"Loading model: {model_path}")
            pipe = StableDiffusionPipeline.from_single_file(model_path, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32)
            device = MODEL_CACHE.device
            pipe = pipe.to(device)
            MODEL_CACHE.set(cache_key, pipe)
        log(f"Generating image for prompt: {prompt} (steps={steps})")
        image = pipe(prompt, num_inference_steps=steps).images[0]
        log("Image generation complete.")
        # Offload after last use if enabled
        if MODEL_CACHE.offload_after_run and session.get_last_use(cache_key) == step_idx:
            MODEL_CACHE.offload(cache_key)
        return image, f"Model: {model_type}/{model_file}\nPrompt: {prompt}\nSteps: {steps}"
    except Exception as e:
        log(f"Error during inference: {e}")
        return Image.new("RGB", (512, 512), color="orange"), f"Error: {e}"

# Dummy workflow registry (replace with dynamic discovery if needed)
WORKFLOWS = {
    "Text-to-Image": {
        "params": [
            {"name": "prompt", "type": "text", "label": "Prompt", "value": "A futuristic cityscape at sunset with flying cars"},
            {"name": "steps", "type": "slider", "label": "Steps", "minimum": 10, "maximum": 100, "value": 30},
            {"name": "model_type", "type": "dropdown", "label": "Model Type", "choices": [
                "checkpoints", "diffusers", "loras", "vae", "embeddings", "unet", "clip", "clip_vision", "style_models"
            ], "value": "checkpoints"},
            {"name": "model_file", "type": "dropdown", "label": "Model File", "choices": [], "value": ""},
        ],
        "run": lambda params, log: run_sd_pipeline(params, log)
    },
    "Image Editing Chain": {
        "params": [
            {"name": "input_image", "type": "image", "label": "Input Image"},
            {"name": "edit_type", "type": "dropdown", "label": "Edit Type", "choices": ["bbox_swap", "segment_swap", "object_removal", "detailer"]},
        ],
        "run": lambda params, log: run_image_editing_chain(params, log)
    },
    "3D Environment from Video (Cosmos)": {
        "params": [
            {"name": "video", "type": "video", "label": "Input Video"}
        ],
        "run": lambda params, log: cosmos_3d_env_run(params, log)
    }
}

# --- Real Image Editing Chain logic ---


def run_image_editing_chain(params, log):
    from PIL import Image
    import numpy as np
    from ai_model.image import mask as mask_mod, inpaint as inpaint_mod
    input_image = params.get("input_image")
    edit_type = params.get("edit_type")
    session = SessionTracker()
    if input_image is None:
        log("No input image provided.")
        return Image.new("RGB", (512, 512), color="red"), "No input image."
    img = input_image.convert("RGB")
    w, h = img.size
    if edit_type == "object_removal":
        mask = mask_mod.create_rect_mask(w, h, (w//4, h//4, 3*w//4, 3*h//4), value=255)
        log("Performing object removal (inpainting central region)...")
        cache_key = ("inpaint", "default")
        step_idx = 0
        inpaint_func = MODEL_CACHE.get(cache_key)
        session.record(cache_key, step_idx)
        if inpaint_func is not None:
            log("Using cached inpaint function/model.")
        else:
            inpaint_func = inpaint_mod.inpaint
            MODEL_CACHE.set(cache_key, inpaint_func)
        out = inpaint_func(img, mask)
        # Offload after last use if enabled
        if MODEL_CACHE.offload_after_run and session.get_last_use(cache_key) == step_idx:
            MODEL_CACHE.offload(cache_key)
        return out, "Object removal (inpainted central region)"
    elif edit_type == "detailer":
        from ai_model.image import manipulation
        log("Applying detailer (sharpen + contrast)...")
        out = manipulation.sharpen(img, percent=200)
        out = manipulation.adjust_contrast(out, 1.3)
        return out, "Detailer: sharpened and contrast enhanced"
    elif edit_type == "bbox_swap":
        log("Swapping left and right halves (bbox_swap demo)...")
        arr = np.array(img)
        mid = w // 2
        arr[:, :mid], arr[:, mid:] = arr[:, mid:].copy(), arr[:, :mid].copy()
        out = Image.fromarray(arr)
        return out, "BBox swap: left/right halves swapped"
    elif edit_type == "segment_swap":
        log("Inverting central segment (segment_swap demo)...")
        arr = np.array(img)
        seg = arr[h//4:3*h//4, w//4:3*w//4]
        arr[h//4:3*h//4, w//4:3*w//4] = 255 - seg
        out = Image.fromarray(arr)
        return out, "Segment swap: central segment inverted"
    else:
        log(f"Unknown edit type: {edit_type}")
        return img, f"Unknown edit type: {edit_type}"

# Resource monitor generator
def resource_monitor_gen(duration=0):
    start_time = time.time()
    cpu_hist, ram_hist, gpu_hist, temp_hist, timestamps = [], [], [], [], []
    while True:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0].load * 100
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            else:
                gpu = 0
                temp = 0
        except Exception:
            gpu = 0
            temp = 0
        elapsed = time.time() - start_time
        cpu_hist.append(cpu)
        ram_hist.append(ram)
        gpu_hist.append(gpu)
        temp_hist.append(temp)
        timestamps.append(elapsed)
        # Plot
        fig, ax = plt.subplots()
        ax.plot(timestamps, cpu_hist, label="CPU %")
        ax.plot(timestamps, ram_hist, label="RAM %")
        ax.plot(timestamps, gpu_hist, label="GPU %")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Usage (%)")
        ax.legend()
        plt.tight_layout()
        stats_md = f"""
        **CPU:** {cpu:.1f}%  
        **RAM:** {ram:.1f}%  
        **GPU:** {gpu:.1f}%  
        **GPU Temp:** {temp}°C  
        **Elapsed:** {elapsed:.1f}s
        """
        import numpy as np
        from io import BytesIO
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        import PIL.Image
        img_arr = np.array(PIL.Image.open(buf))
        plt.close(fig)
        yield img_arr, stats_md
        if duration and elapsed > duration:
            break
        time.sleep(1)

def run_workflow_thread(workflow_name, params, q):
    """
    Workflow runner (runs in a thread, puts outputs/logs in a queue).

    To expand for custom workflows: in your workflow function, use
      model = MODEL_CACHE.get(cache_key)
      if model is None: ... load model ... MODEL_CACHE.set(cache_key, model)
    This ensures all local workflows benefit from LRU caching and memory limits.
    """
    log = lambda msg: q.put(("log", msg))
    wf = WORKFLOWS[workflow_name]
    img, logmsg = wf["run"](params, log)
    q.put(("output", img, logmsg))

# Gradio app
def gradio_app():
    import glob
    import importlib.util
    from pathlib import Path
    with gr.Blocks() as demo:
        gr.Markdown("# Multi-Agent Workflow GUI with Resource Monitor")
        with gr.Tab("Workflows"):
            with gr.Row():
                with gr.Column(scale=2):
                    # Workflow navigation module
                    gr.Markdown("### Example Workflows Navigation")
                    example_files = sorted([str(f) for f in Path("examples").glob("*.py") if not f.name.endswith("workflow_gui_gradio.py")])
                    example_names = [Path(f).stem for f in example_files]
                    workflow_nav = gr.Dropdown(example_names, label="Available Example Workflows", value=example_names[0] if example_names else None)
                    nav_output = gr.Textbox(label="Workflow Description", lines=3, interactive=False)
                    def show_example_desc(selected):
                        file = next((f for f in example_files if Path(f).stem == selected), None)
                        if not file:
                            return "Not found."
                        with open(file, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.strip().startswith('"""'):
                                    desc = [line.strip().strip('"')]
                                    for l in f:
                                        if l.strip().startswith('"""'):
                                            break
                                        desc.append(l.rstrip())
                                    return "\n".join(desc)
                        return "No docstring found."
                    workflow_nav.change(show_example_desc, inputs=workflow_nav, outputs=nav_output)
                    launch_btn = gr.Button("Run Selected Workflow (CLI)")
                    def run_example(selected):
                        file = next((f for f in example_files if Path(f).stem == selected), None)
                        if not file:
                            return "File not found."
                        # Run as subprocess (CLI)
                        import subprocess
                        try:
                            result = subprocess.run([sys.executable, file], capture_output=True, text=True, timeout=60)
                            return result.stdout + "\n" + result.stderr
                        except Exception as e:
                            return f"Error: {e}"
                    nav_cli_output = gr.Textbox(label="Workflow Output (CLI)", lines=8, interactive=False)
                    launch_btn.click(run_example, inputs=workflow_nav, outputs=nav_cli_output)
                    gr.Markdown("---")
                # input("Gradio app starting...")  # Removed to allow Gradio to launch
                workflow_sel = gr.Dropdown(list(WORKFLOWS.keys()), label="Select Workflow", value=list(WORKFLOWS.keys())[0])
                param_elems = {}
                param_box = gr.Column()
                run_btn = gr.Button("Run Workflow")
                output_img = gr.Image(label="Output Image")
                output_log = gr.Textbox(label="Logs/Output", lines=4)
                with gr.Column(scale=1):
                    gr.Markdown("## Resource Usage (Live)")
                    res_plot = gr.Image(label="Resource Usage Over Time", type="numpy")
                    res_stats = gr.Markdown(label="Current Stats")
                    res_btn = gr.Button("Start Resource Monitor")
        # --- Settings Tab for Cache Config ---
        with gr.Tab("Settings"):
            gr.Markdown("### Model Cache Settings")
            vram_slider = gr.Slider(label="Max VRAM for Model Cache (GB)", minimum=1, maximum=40, value=CACHE_CONFIG["max_vram_gb"], step=1)
            device_dropdown = gr.Dropdown(label="Device", choices=["cuda", "cpu"], value=CACHE_CONFIG["device"])
            offload_toggle = gr.Checkbox(label="Offload Models After Last Use", value=CACHE_CONFIG["offload_after_run"])
            update_btn = gr.Button("Update Cache Settings")
            cache_status = gr.Textbox(label="Current Cache Config", value=str(CACHE_CONFIG), interactive=False)
            def update_settings(vram, device, offload):
                update_cache_config(max_vram_gb=vram, device=device, offload_after_run=offload)
                return str(CACHE_CONFIG)
            update_btn.click(update_settings, inputs=[vram_slider, device_dropdown, offload_toggle], outputs=cache_status)
        # Dynamic parameter UI
        import glob
        def get_model_files(model_type):
            base = "D:/comfyui/resources/comfyui/models/"
            folder = os.path.join(base, model_type)
            if not os.path.isdir(folder):
                return []
            files = glob.glob(os.path.join(folder, "*.safetensors")) + glob.glob(os.path.join(folder, "*.pth")) + glob.glob(os.path.join(folder, "*.pt"))
            return [os.path.basename(f) for f in files]

        def update_params(wf_name, model_type_value=None):
            wf = WORKFLOWS[wf_name]
            elems = []
            for p in wf["params"]:
                if p["type"] == "text":
                    elems.append(gr.Textbox(label=p["label"], value=p.get("value", ""), interactive=True))
                elif p["type"] == "slider":
                    elems.append(gr.Slider(label=p["label"], minimum=p["minimum"], maximum=p["maximum"], value=p.get("value", 0), interactive=True))
                elif p["type"] == "dropdown":
                    if p["name"] == "model_file":
                        # Dynamically update model_file choices based on model_type_value
                        model_type = model_type_value or wf["params"][2]["value"]
                        files = get_model_files(model_type)
                        elems.append(gr.Dropdown(label=p["label"], choices=files, value=files[0] if files else "", interactive=True))
                    elif p["name"] == "model_type":
                        elems.append(gr.Dropdown(label=p["label"], choices=p["choices"], value=p["value"], interactive=True))
                    else:
                        elems.append(gr.Dropdown(label=p["label"], choices=p["choices"], value=p["choices"][0], interactive=True))
                elif p["type"] == "image":
                    elems.append(gr.Image(label=p["label"], interactive=True))
                elif p["type"] == "video":
                    elems.append(gr.Video(label=p["label"], interactive=True))
            return elems
        param_elems_list = update_params(list(WORKFLOWS.keys())[0])
        param_box.children = param_elems_list
        # When workflow changes, update params
        workflow_sel.change(lambda wf: update_params(wf), inputs=workflow_sel, outputs=param_box)
        # When model_type changes, update model_file dropdown
        def on_model_type_change(model_type):
            return update_params("Text-to-Image", model_type_value=model_type)
        # Attach to the model_type dropdown (assumes 3rd param is model_type)
        if len(param_box.children) > 2:
            param_box.children[2].change(on_model_type_change, inputs=param_box.children[2], outputs=param_box)
        # Run workflow
        def run_workflow(wf_name, *args):
            wf = WORKFLOWS[wf_name]
            params = {}
            for i, p in enumerate(wf["params"]):
                params[p["name"]] = args[i]
            q = Queue()
            t = Thread(target=run_workflow_thread, args=(wf_name, params, q))
            t.start()
            logs = ""
            img = None
            while t.is_alive() or not q.empty():
                while not q.empty():
                    item = q.get()
                    if item[0] == "log":
                        logs += str(item[1]) + "\n"
                    elif item[0] == "output":
                        img, logmsg = item[1], item[2]
                        logs += str(logmsg) + "\n"
                time.sleep(0.2)
                yield img, logs
            yield img, logs
        run_btn.click(run_workflow, inputs=[workflow_sel]+param_box.children, outputs=[output_img, output_log])
        # Resource monitor
        res_btn.click(resource_monitor_gen, outputs=[res_plot, res_stats], queue=True)
    return demo

if __name__ == "__main__":
    gradio_app().launch(
        pwa=True,
        favicon_path="icons/icon32.png",
        show_error=True,
        debug=True,
        server_name="0.0.0.0",
        server_port=7860
    )
