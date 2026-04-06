"""Workflows sub-package."""

from smolvlm2_wrapper.workflows.base import Workflow, Step
from smolvlm2_wrapper.workflows.examples import (
    PhotoEnhancementWorkflow,
    VideoAnalysisWorkflow,
    PromptGenerationWorkflow,
    InpaintingWorkflow,
    VideoEditWorkflow,
)

__all__ = [
    "Workflow",
    "Step",
    "PhotoEnhancementWorkflow",
    "VideoAnalysisWorkflow",
    "PromptGenerationWorkflow",
    "InpaintingWorkflow",
    "VideoEditWorkflow",
]
