"""
Gradio interface for creating 3D environments from real-life videos.
- Upload a video, process to 3D scene (mesh, textures)
- Navigate with a virtual camera
- Integrates with modular agent architecture
"""
import gradio as gr
from smolvlm2_wrapper.image.image_to_3d import image_to_3d  # Actual function name

from smolvlm2_wrapper.cosmos_3d_env_workflow import cosmos_3d_env_run
import io

def video_to_3d(video_file, log_callback):
    params = {'video': video_file}
    mesh_path, status = cosmos_3d_env_run(params, log_callback)
    return mesh_path, status

def launch_3d_env_gradio():
    import threading
    import time
    from smolvlm2_wrapper.redis_coordination import RedisCoordinator
    import gradio as gr

    redis_messages = []
    redis_lock = threading.Lock()
    coordinator = RedisCoordinator(agent_id='gradio-viewer')
    def on_redis_message(msg):
        with redis_lock:
            redis_messages.append(msg)
            # Keep only last 100 messages
            if len(redis_messages) > 100:
                redis_messages.pop(0)
    coordinator.listen(on_redis_message)

    def get_redis_messages():
        with redis_lock:
            return '\n'.join([str(m) for m in redis_messages])

    with gr.Blocks() as demo:
        gr.Markdown("# 3D Environment from Video")
        video_input = gr.Video(label="Upload Video")
        mesh_output = gr.File(label="3D Mesh Output (.obj)")
        log_output = gr.Textbox(label="Logs", lines=8)
        run_btn = gr.Button("Generate 3D Environment")

        gr.Markdown("## Redis Message Viewer")
        redis_box = gr.Textbox(label="Redis Messages", lines=12, interactive=False)
        refresh_btn = gr.Button("Refresh Redis Messages")
        refresh_btn.click(lambda: get_redis_messages(), outputs=redis_box)

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
