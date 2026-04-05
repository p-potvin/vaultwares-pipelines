# Pipeline: Object Removal (Inpainting)

## Overview
This pipeline describes how to remove objects from images using inpainting with Stable Diffusion or similar tools.

## Steps
1. **Install Stable Diffusion or inpainting tool**
   - Use AUTOMATIC1111 WebUI, ComfyUI, or Diffusers for inpainting.
   - Example: `pip install diffusers` or follow ComfyUI setup instructions.

2. **Prepare input image and mask**
   - Select the image and create a mask (white = area to remove, black = keep).
   - Save both as PNG files.

3. **Run inpainting**
   - Using Diffusers (Python):
     ```python
     from diffusers import StableDiffusionInpaintPipeline
     import torch
     pipe = StableDiffusionInpaintPipeline.from_pretrained('runwayml/stable-diffusion-inpainting', torch_dtype=torch.float16)
     pipe = pipe.to('cuda')
     result = pipe(image=input_image, mask_image=mask_image).images[0]
     result.save('output.png')
     ```
   - Or use ComfyUI/Stable Diffusion WebUI for a GUI workflow.

4. **Review and refine**
   - Inspect the output and adjust the mask or settings as needed.

## References
- https://github.com/huggingface/diffusers
- https://github.com/comfyanonymous/ComfyUI
- https://github.com/AUTOMATIC1111/stable-diffusion-webui
