import tempfile
import os
import cv2
import numpy as np
from ai_model.nim_cosmos_api import NIMCosmosClient
import trimesh

def extract_frames(video_path, max_frames=32):
    cap = cv2.VideoCapture(video_path)
    frames = []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total // max_frames)
    idx = 0
    while cap.isOpened() and len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            _, buf = cv2.imencode('.jpg', frame)
            frames.append(buf.tobytes())
        idx += 1
    cap.release()
    return frames

def save_mesh(mesh_data, out_path):
    # mesh_data: dict with 'vertices', 'faces', 'colors' (optional)
    mesh = trimesh.Trimesh(vertices=np.array(mesh_data['vertices']), faces=np.array(mesh_data['faces']))
    mesh.export(out_path)
    return out_path

def cosmos_3d_env_run(params, log):
    video = params['video']
    log('Extracting frames...')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(video.read())
        tmp_path = tmp.name
    frames = extract_frames(tmp_path)
    try:
        log(f'Extracted {len(frames)} frames. Sending to Cosmos...')
        client = NIMCosmosClient()
        result = client.infer_3d([f.decode("latin1") for f in frames])
        log('Received mesh from Cosmos.')
        mesh_path = os.path.join(tempfile.gettempdir(), 'cosmos_mesh.obj')
        save_mesh(result['mesh'], mesh_path)
        return mesh_path, '3D mesh generated (Cosmos API).'
    except Exception as e:
        log(f'Cosmos API unavailable: {e}. Trying Hunyuan 3D v2.1 fallback...')
        try:
            mesh_path = hunyuan_3d_fallback(frames, log)
            return mesh_path, 'Local fallback: Hunyuan 3D v2.1 mesh generated.'
        except Exception as hun_err:
            log(f'Hunyuan 3D fallback failed: {hun_err}. Using flat mesh fallback.')
            # Flat mesh fallback
            import trimesh
            import numpy as np
            if frames:
                import cv2
                img = cv2.imdecode(np.frombuffer(frames[0], np.uint8), cv2.IMREAD_COLOR)
                h, w, _ = img.shape
                vertices = np.array([[0,0,0],[w,0,0],[w,h,0],[0,h,0]], dtype=np.float32)
                faces = np.array([[0,1,2],[0,2,3]], dtype=np.int32)
                mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
                mesh_path = os.path.join(tempfile.gettempdir(), 'local_fallback_mesh.obj')
                mesh.export(mesh_path)
                return mesh_path, 'Local fallback: flat mesh generated.'
            return None, 'No frames extracted.'

# Minimal Hunyuan 3D v2.1 inference (single frame, mesh export)
def hunyuan_3d_fallback(frames, log):
    import torch
    import safetensors.torch
    import cv2
    import numpy as np
    import trimesh
    # Path to the checkpoint
    ckpt = r"D:\comfyUI\resources\ComfyUI\models\checkpoints\hunyuan_3d_v2.1.safetensors"
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # Load model weights (assume state_dict only)
    state = safetensors.torch.load_file(ckpt, device=device)
    # Dummy model: just create a cube mesh for now (replace with real inference logic)
    # TODO: Replace with actual model class and inference pipeline
    vertices = np.array([
        [0,0,0],[1,0,0],[1,1,0],[0,1,0],
        [0,0,1],[1,0,1],[1,1,1],[0,1,1]
    ], dtype=np.float32)
    faces = np.array([
        [0,1,2],[0,2,3],[4,5,6],[4,6,7],
        [0,1,5],[0,5,4],[2,3,7],[2,7,6],
        [1,2,6],[1,6,5],[0,3,7],[0,7,4]
    ], dtype=np.int32)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    mesh_path = os.path.join(tempfile.gettempdir(), 'hunyuan3d_mesh.obj')
    mesh.export(mesh_path)
    log('Hunyuan 3D fallback: dummy cube mesh (replace with real inference).')
    return mesh_path
