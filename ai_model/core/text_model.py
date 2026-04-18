
"""
Generic text model wrapper for HuggingFace-compatible models (multi-modal or text-only).

This module provides :class:`TextModelWrapper`, a concrete implementation of
:class:`~ai_model.core.model.BaseModelWrapper` that integrates any HuggingFace-compatible
text generation model for multi-modal or text-only inference.

Supports:
* **image–text** inputs (single or multiple images)
* **video** inputs (sequences of frames treated as images)
* **text-only** inputs

Example – image captioning::

    from ai_model import TextModelWrapper
    from PIL import Image

    model = TextModelWrapper(model_id="HuggingFaceTB/AIModel-500M-Video-Instruct")
    caption = model.caption(Image.open("photo.jpg"))
    print(caption)

Example – text generation::

    model = TextModelWrapper(model_id="gpt2")
    text = model.generate("Write a poem about the sea.")
    print(text)
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Union

from PIL import Image


from ai_model.core.config import ModelConfig
from ai_model.core.model import BaseModelWrapper

logger = logging.getLogger(__name__)


_DEFAULT_MODEL_ID = "gpt2"



class TextModelWrapper(BaseModelWrapper):
    """Generic wrapper for any HuggingFace-compatible text generation model.

    Parameters
    ----------
    config:
        Optional :class:`ModelConfig`.  Defaults to GPT-2 on the best available device.

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
        """Load the AutoTokenizer and AutoModelForCausalLM or multimodal model from HuggingFace."""
        import torch
        from transformers import (
            AutoTokenizer,
            AutoModelForCausalLM,
            AutoModelForVision2Seq,
            AutoProcessor
        )

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

        # Try to load as a multimodal model first, fallback to text-only
        try:
            self._processor = AutoProcessor.from_pretrained(
                self.config.model_id,
                **({} if not self.config.cache_dir else {"cache_dir": self.config.cache_dir}),
            )
            self._model = AutoModelForVision2Seq.from_pretrained(
                self.config.model_id,
                **load_kwargs,
            ).to(self.device)
        except Exception:
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_id,
                **({} if not self.config.cache_dir else {"cache_dir": self.config.cache_dir}),
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                self.config.model_id,
                **load_kwargs,
            ).to(self.device)
            self._processor = None

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
        """Run inference and return a text string (supports text-only and multi-modal)."""
        if not self._loaded:
            self.load()

        import torch

        if self._processor is not None:
            # Multi-modal (image/video/text)
            content: list = []
            for img in (images or []):
                content.append({"type": "image"})
            for _ in (videos or []):
                content.append({"type": "video"})
            content.append({"type": "text", "text": prompt})
            messages = [{"role": "user", "content": content}]
            text_prompt = self._processor.apply_chat_template(
                messages, add_generation_prompt=True
            )
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
            input_len = inputs["input_ids"].shape[1]
            new_ids = output_ids[:, input_len:]
            return self._processor.decode(new_ids[0], skip_special_tokens=True)
        else:
            # Text-only model
            input_ids = self._tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)
            gen_kwargs = self.config.generation_kwargs()
            gen_kwargs.update(kwargs)
            with torch.no_grad():
                output_ids = self._model.generate(input_ids, **gen_kwargs)
            return self._tokenizer.decode(output_ids[0], skip_special_tokens=True)

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
        
        if style in style_prompts:
            prompt = style_prompts[style]
        else:   
            prompt = style_prompts.get(style, style_prompts["detailed"])  # default to "detailed"
    
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

            from ai_model.video.utils import sample_frames
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
        """Convenience shim – delegates to :func:`ai_model.video.utils.sample_frames`.

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
        from ai_model.video.utils import sample_frames
        return sample_frames(video_path, n=max_frames)
