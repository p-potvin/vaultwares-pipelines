from pydantic import BaseModel, Field
from typing import Optional, List, Tuple, Any

class ImageContext(BaseModel):
    image_path: str
    output_path: Optional[str]
    width: Optional[int] = 1024
    height: Optional[int] = 768
    sharpen_percent: Optional[int] = 150
    brightness: Optional[float] = 1.1
    contrast: Optional[float] = 1.2
    mask_box: Optional[Tuple[int, int, int, int]]
    feather: Optional[float] = 3.0
    image: Optional[Any]
    mask: Optional[Any]
    caption: Optional[str]

class VideoContext(BaseModel):
    video_path: str
    output_path: Optional[str]
    n_frames: Optional[int] = 8
    caption_style: Optional[str] = "brief"
    description_focus: Optional[str] = "action"
    trim_start: Optional[int] = 0
    trim_end: Optional[int]
    width: Optional[int]
    height: Optional[int]
    effect: Optional[Any]
    fps: Optional[float] = 24.0
    frames: Optional[List[Any]]
    description: Optional[str]
    captions: Optional[List[str]]

class TextContext(BaseModel):
    prompt: Optional[str]
    style: Optional[str] = "detailed"
    image: Optional[Any]
    video: Optional[Any]
    answer: Optional[str]
    enhanced_prompt: Optional[str]

class WorkflowContext(BaseModel):
    steps: List[str]
    context: dict
    result: Optional[Any]

# Add more schemas as needed for agent communication
