"""
Gradio interface for creating 3D environments from real-life videos.
- Upload a video, process to 3D scene (mesh, textures)
- Navigate with a virtual camera
- Integrates with modular agent architecture
"""
import gradio as gr
from ai_model.image.image_to_3d import image_to_3d  # Actual function name

from ai_model.cosmos_3d_env_workflow import cosmos_3d_env_run
import io

def video_to_3d(video_file, log_callback):
    params = {'video': video_file}
    mesh_path, status = cosmos_3d_env_run(params, log_callback)
    return mesh_path, status

def launch_3d_env_gradio():
    with gr.Blocks() as demo:
        gr.Markdown("# 3D Environment from Video")
        video_input = gr.Video(label="Upload Video")
        mesh_output = gr.File(label="3D Mesh Output (.obj)")
        log_output = gr.Textbox(label="Logs", lines=8)
        run_btn = gr.Button("Generate 3D Environment")

        def process(video):
            logs = []
            def log_callback(msg):
                logs.append(str(msg))
            try:
                mesh_path, status = video_to_3d(video, log_callback)
                logs.append(status)
                return mesh_path, "\n".join(logs)
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                logs.append(f"ERROR: {e}\n{tb}")
                return None, "\n".join(logs)

        run_btn.click(process, inputs=video_input, outputs=[mesh_output, log_output])
    return demo

if __name__ == "__main__":
    launch_3d_env_gradio().launch()
