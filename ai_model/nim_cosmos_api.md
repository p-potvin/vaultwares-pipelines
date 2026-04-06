# NVIDIA NIM Cosmos API Wrapper

This module provides a Python client for calling the NVIDIA NIM Cosmos microservice for 3D environment generation from video frames.

## Usage

1. Set your NVIDIA NIM API key in the environment:
   ```bash
   export NIM_API_KEY=your_api_key_here
   ```
2. (Optional) Set a custom API URL:
   ```bash
   export NIM_COSMOS_API_URL=https://nim.nvidia.com/api/cosmos/v1/infer
   ```
3. Use the `NIMCosmosClient` in your pipeline:
   ```python
   from ai_model.nim_cosmos_api import NIMCosmosClient
   client = NIMCosmosClient()
   result = client.infer_3d([frame1_bytes, frame2_bytes, ...])
   # result contains depth, pose, mesh, etc.
   ```

## Integration
- Designed for use in the Gradio 3D environment UI and other workflows.
- Handles authentication and error checking.

---

**Status:** Scaffolded, ready for integration and testing.
