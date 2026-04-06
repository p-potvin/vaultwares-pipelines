"""
Module: image_to_3d.py
---------------------
Generate a 3D mesh (with textures) from a single image.

Usage:
    python image_to_3d.py --input <image> --output <output_dir>

Dependencies:
    - open3d
    - trimesh
    - numpy
    - Pillow

This is a scaffold. Actual 3D reconstruction requires depth estimation and mesh generation.
"""
import argparse
from pathlib import Path
from PIL import Image
import numpy as np
import open3d as o3d
import trimesh

def image_to_3d(input_image, output_dir):
    # Load image
    img = Image.open(input_image).convert("RGB")
    img_np = np.array(img)
    h, w, _ = img_np.shape

    # Placeholder: create a flat plane mesh with the image as texture
    vertices = np.array([
        [0, 0, 0],
        [w, 0, 0],
        [w, h, 0],
        [0, h, 0],
    ], dtype=np.float32)
    faces = np.array([
        [0, 1, 2],
        [0, 2, 3],
    ], dtype=np.int32)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    # Save mesh as .obj
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    mesh_path = output_dir / "mesh.obj"
    mesh.export(mesh_path)
    # Save texture
    texture_path = output_dir / "texture.png"
    img.save(texture_path)
    print(f"Saved mesh to {mesh_path} and texture to {texture_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a 3D mesh from an image.")
    parser.add_argument("--input", required=True, help="Input image file")
    parser.add_argument("--output", required=True, help="Output directory for mesh and texture")
    args = parser.parse_args()
    image_to_3d(args.input, args.output)
