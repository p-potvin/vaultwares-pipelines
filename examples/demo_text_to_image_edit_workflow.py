"""
Demo: Complex text-to-image workflow with image editing and detailer chain.
This script instantiates agents, connects them via shared context and event bus,
and executes a multi-stage workflow: text→image→edit (bbox/segment swap, object removal, detailer).
"""
from ai_model.shared_context import SharedContext
from ai_model.agent_interface import AgentInterface
from ai_model.event_bus import EventBus
from ai_model.central_error_logger import CentralErrorLogger
# Assume these agent classes exist and are imported:
# from ai_model.agent_text import TextProcessor
# from ai_model.agent_image import ImageProcessor
# from ai_model.workflow_export_agent import WorkflowExportAgent


# Use real model-powered agents
from ai_model import GenericTextModelWrapper
from ai_model.text.processor import TextProcessor as RealTextProcessor
from ai_model.image.processor import ImageProcessor as RealImageProcessor
from PIL import Image

# Instantiate real model
model = GenericTextModelWrapper()
text_agent = RealTextProcessor(model=model)
image_agent = RealImageProcessor()

class WorkflowExportAgent:
    def __init__(self, shared_context):
        self.shared_context = shared_context
    def export_to_comfyui(self, workflow_dict):
        # Simulate export
        return {'success': True, 'comfyui_workflow': workflow_dict}

# Setup shared context and error logger
shared_context = SharedContext(workflow_id='demo1')
CentralErrorLogger(shared_context)


workflow_exporter = WorkflowExportAgent(shared_context)


# 1. Text-to-image prompt engineering (real model)
prompt = "A futuristic cityscape at sunset with flying cars"
engineered_prompt = text_agent.enhance_prompt(prompt)

# 2. Image generation and editing chain (simulate with blank image for demo)
img = Image.new("RGB", (512, 512), color="white")
edits1 = ["bbox swapped"]
edits2 = ["segments swapped"]
edits3 = ["object removed"]
edits4 = ["detailer chain applied"]

# 3. Aggregate workflow for export
workflow_dict = {
    'prompt': engineered_prompt,
    'image': img,
    'edits': edits1 + edits2 + edits3 + edits4
}
export_result = workflow_exporter.export_to_comfyui(workflow_dict)

# 4. Print results and error log
print("Workflow export result:", export_result)
print("Error log:", shared_context.errors)
print("Agent contexts:", shared_context.agents)
