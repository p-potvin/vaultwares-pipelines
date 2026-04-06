# Image to 3D Model Module

Generate a 3D mesh (with textures) from a single image.

## Usage

```bash
python -m smolvlm2_wrapper.image.image_to_3d --input <image> --output <output_dir>
```

- `--input`: Path to the input image file
- `--output`: Output directory for mesh (.obj) and texture (.png)

## Description
- This module creates a flat plane mesh with the input image as a texture (scaffold for future 3D reconstruction).
- Dependencies: open3d, trimesh, numpy, Pillow

## Example
```bash
python -m smolvlm2_wrapper.image.image_to_3d --input ./photo.jpg --output ./3d_output
```

## Notes
- For true 3D reconstruction, integrate depth estimation and mesh generation in future versions.
