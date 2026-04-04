# Gradio 3D Environment Workflow UI Instructions

## How to Access the Gradio UI

1. Open a terminal in the project root directory.
2. Run:

    python examples/workflow_gui_gradio.py

3. After a few seconds, you will see output like:

    * Running on local URL:  http://127.0.0.1:7860

4. Open your web browser and go to the URL above (http://127.0.0.1:7860).
5. Select the "3D Environment from Video (Cosmos)" workflow, upload a video, and click "Run Workflow".

- If the Cosmos API is unavailable, a local fallback mesh will be generated from the first video frame.
- For best results, use the Cosmos API with your NIM credentials when available.
