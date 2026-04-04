"""
SmolVLM2-500M-Video-Instruct wrapper.

This module provides :class:`SmolVLM2Wrapper`, a concrete implementation of
:class:`~smolvlm2_wrapper.core.model.BaseModelWrapper` that integrates
HuggingFace's SmolVLM2-500M-Video-Instruct model for multi-modal inference.

The model supports
* **image–text** inputs (single or multiple images)
* **video** inputs (sequences of frames treated as images)
* **text-only** inputs

Example – image captioning::

    from smolvlm2_wrapper import SmolVLM2Wrapper
    from PIL import Image

    model = SmolVLM2Wrapper()
    caption = model.caption(Image.open("photo.jpg"))
    print(caption)

Example – visual question answering::

    answer = model.answer_question(
        "What objects are in the background?",
        images=[Image.open("photo.jpg")],
    )

Example – video description::

    frames = model.extract_video_frames("clip.mp4", max_frames=8)
    description = model.describe_video(frames)
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Union

from PIL import Image

from smolvlm2_wrapper.core.config import ModelConfig
from smolvlm2_wrapper.core.model import BaseModelWrapper

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_ID = "HuggingFaceTB/SmolVLM2-500M-Video-Instruct"


class SmolVLM2Wrapper(BaseModelWrapper):
    """Wrapper around SmolVLM2-500M-Video-Instruct.

    Parameters
    ----------
    config:
        Optional :class:`ModelConfig`.  Defaults to SmolVLM2-500M on the
        best available device.

    Notes
    -----
    The model and processor are loaded **lazily** – the first call to any
    inference method triggers :meth:`load`.  Call :meth:`load` explicitly if
    you want to pay the loading cost upfront.
    """

    DEFAULT_CONFIG = ModelConfig(model_id=_DEFAULT_MODEL_ID)

    # ------------------------------------------------------------------ #
    # loading                                                              #
    # ------------------------------------------------------------------ #

    def _load_model(self) -> None:
        """Load the AutoProcessor and AutoModelForVision2Seq from HuggingFace."""
        import torch
        from transformers import AutoProcessor, AutoModelForVision2Seq

        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        torch_dtype = dtype_map.get(self.config.dtype, torch.float32)

        load_kwargs: dict = {
            "torch_dtype": torch_dtype,
            "_attn_implementation": "eager",
        }
        if self.config.cache_dir:
            load_kwargs["cache_dir"] = self.config.cache_dir
        if self.config.low_memory:
            load_kwargs["low_cpu_mem_usage"] = True
        load_kwargs.update(self.config.extra)

        self._processor = AutoProcessor.from_pretrained(
            self.config.model_id,
            **({} if not self.config.cache_dir else {"cache_dir": self.config.cache_dir}),
        )
        self._model = AutoModelForVision2Seq.from_pretrained(
            self.config.model_id,
            **load_kwargs,
        ).to(self.device)

    # ------------------------------------------------------------------ #
    # core inference                                                       #
    # ------------------------------------------------------------------ #

    def generate(
        self,
        prompt: str,
        images: Optional[List[Image.Image]] = None,
        videos: Optional[List[List[Image.Image]]] = None,
        **kwargs: Any,
    ) -> str:
        """Run SmolVLM2 inference and return a text string.

        The method builds a chat-style message list from *prompt* and the
        optional visual inputs, tokenises them with the AutoProcessor, runs
        ``model.generate``, then decodes and returns the new tokens only.

        Parameters
        ----------
        prompt:
            Instruction or question.
        images:
            Zero or more PIL images to include.
        videos:
            Zero or more videos, each represented as a list of PIL frames.
            Frames are sampled / passed through the processor automatically.
        **kwargs:
            Override generation parameters (e.g. ``max_new_tokens=512``).

        Returns
        -------
        str
            Model response text (input tokens stripped).
        """
        if not self._loaded:
            self.load()

        import torch

        content: list = []

        # attach image tokens
        for img in (images or []):
            content.append({"type": "image"})

        # attach video tokens (video = list of PIL frames)
        for _ in (videos or []):
            content.append({"type": "video"})

        content.append({"type": "text", "text": prompt})

        messages = [{"role": "user", "content": content}]

        # build the text prompt via apply_chat_template
        text_prompt = self._processor.apply_chat_template(
            messages, add_generation_prompt=True
        )

        # collect flat PIL inputs for the processor
        flat_images = list(images or [])
        flat_video_frames = list(videos or [])

        processor_kwargs: dict = {"text": text_prompt, "return_tensors": "pt"}
        if flat_images:
            processor_kwargs["images"] = flat_images
        if flat_video_frames:
            processor_kwargs["videos"] = flat_video_frames

        inputs = self._processor(**processor_kwargs).to(self.device)

        gen_kwargs = self.config.generation_kwargs()
        gen_kwargs.update(kwargs)

        with torch.no_grad():
            output_ids = self._model.generate(**inputs, **gen_kwargs)

        # strip input tokens from output
        input_len = inputs["input_ids"].shape[1]
        new_ids = output_ids[:, input_len:]
        return self._processor.decode(new_ids[0], skip_special_tokens=True)

    # ------------------------------------------------------------------ #
    # convenience high-level methods                                       #
    # ------------------------------------------------------------------ #

    def caption(
        self,
        image: Image.Image,
        style: str = "detailed",
        **kwargs: Any,
    ) -> str:
        """Generate a natural-language caption for *image*.

        Parameters
        ----------
        image:
            Input PIL image.
        style:
            ``"brief"`` – one-sentence caption.
            ``"detailed"`` – thorough description (default).
            ``"tags"`` – comma-separated keyword list.

        Returns
        -------
        str
            Caption text.

        Example::

            caption = wrapper.caption(Image.open("beach.jpg"), style="brief")
        """
        style_prompts = {
            "brief": "Describe this image in one sentence.",
            "detailed": (
                "Provide a detailed description of this image, including objects, "
                "colours, spatial relationships, and any text visible."
            ),
            "tags": (
                "List the main subjects and attributes in this image as "
                "comma-separated keywords."
            ),
        }
        prompt = style_prompts.get(style, style_prompts["detailed"])
        return self.generate(prompt, images=[image], **kwargs)

    def answer_question(
        self,
        question: str,
        images: Optional[List[Image.Image]] = None,
        **kwargs: Any,
    ) -> str:
        """Visual question answering.

        Parameters
        ----------
        question:
            Natural-language question about the visual content.
        images:
            One or more PIL images providing visual context.

        Returns
        -------
        str
            Model answer.

        Example::

            answer = wrapper.answer_question(
                "How many people are in the image?",
                images=[Image.open("crowd.jpg")],
            )
        """
        return self.generate(question, images=images, **kwargs)

    def describe_video(
        self,
        frames: List[Image.Image],
        prompt: str = "Describe what is happening in this video.",
        **kwargs: Any,
    ) -> str:
        """Generate a natural-language description of a video clip.

        Parameters
        ----------
        frames:
            Ordered list of PIL frames sampled from the video.
        prompt:
            Custom instruction.

        Returns
        -------
        str
            Video description.

        Example::

            from smolvlm2_wrapper.video.utils import sample_frames
            frames = sample_frames("clip.mp4", n=8)
            desc = wrapper.describe_video(frames)
        """
        return self.generate(prompt, videos=[frames], **kwargs)

    def enhance_prompt(
        self,
        prompt: str,
        image: Optional[Image.Image] = None,
        **kwargs: Any,
    ) -> str:
        """Rewrite and enrich a text prompt to make it more descriptive.

        Optionally grounds the enhancement in a reference image.

        Parameters
        ----------
        prompt:
            The original (possibly terse) prompt.
        image:
            Optional reference image to guide the enrichment.

        Returns
        -------
        str
            Enhanced prompt string.

        Example::

            better = wrapper.enhance_prompt(
                "a dog running",
                image=Image.open("dog.jpg"),
            )
        """
        instruction = (
            f'Rewrite and significantly expand the following image-generation prompt '
            f'to be more descriptive, vivid, and detailed while preserving its intent.  '
            f'Return only the improved prompt without explanation.\n\nOriginal: "{prompt}"'
        )
        images = [image] if image is not None else None
        return self.generate(instruction, images=images, **kwargs)

    def extract_video_frames(
        self,
        video_path: str,
        max_frames: int = 8,
    ) -> List[Image.Image]:
        """Convenience shim – delegates to :func:`smolvlm2_wrapper.video.utils.sample_frames`.

        Parameters
        ----------
        video_path:
            Path to a local video file.
        max_frames:
            Maximum number of frames to sample.

        Returns
        -------
        List[PIL.Image.Image]
            Evenly-sampled frames.
        """
        from smolvlm2_wrapper.video.utils import sample_frames
        return sample_frames(video_path, n=max_frames)
