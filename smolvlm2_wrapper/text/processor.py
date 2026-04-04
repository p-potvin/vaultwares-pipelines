"""
High-level :class:`TextProcessor` for text and prompt operations.

Usage::

    from smolvlm2_wrapper import SmolVLM2Wrapper
    from smolvlm2_wrapper.text.processor import TextProcessor
    from PIL import Image

    model = SmolVLM2Wrapper()
    tp = TextProcessor(model=model)

    caption = tp.caption(Image.open("photo.jpg"), style="detailed")
    enhanced = tp.enhance_prompt("a beach sunset")
    answer  = tp.vqa("How many people?", images=[Image.open("crowd.jpg")])
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from PIL import Image

from smolvlm2_wrapper.text.prompts import (
    build_caption_prompt,
    build_vqa_prompt,
    build_enhancement_prompt,
    build_video_description_prompt,
    STYLE_PROMPTS,
)

logger = logging.getLogger(__name__)


class TextProcessor:
    """Fluent text-generation interface backed by any model wrapper.

    Parameters
    ----------
    model:
        Any object with a compatible ``generate(prompt, images, videos)``
        method (e.g. :class:`~smolvlm2_wrapper.core.smolvlm2.SmolVLM2Wrapper`).
    """

    def __init__(self, model=None) -> None:
        self._model = model

    def _require_model(self) -> None:
        if self._model is None:
            raise RuntimeError(
                "No model attached.  Pass model=SmolVLM2Wrapper() to TextProcessor."
            )

    # ------------------------------------------------------------------ #
    # captioning                                                           #
    # ------------------------------------------------------------------ #

    def caption(
        self,
        image: Image.Image,
        style: str = "detailed",
        **kwargs: Any,
    ) -> str:
        """Generate a caption for *image*.

        Parameters
        ----------
        image:
            PIL image.
        style:
            One of ``"brief"``, ``"detailed"``, ``"tags"``, ``"cinematic"``,
            ``"sd_prompt"``.

        Returns
        -------
        str
            Caption text.

        Example::

            caption = tp.caption(Image.open("photo.jpg"), style="sd_prompt")
        """
        self._require_model()
        prompt = build_caption_prompt(style)
        return self._model.generate(prompt, images=[image], **kwargs)

    # ------------------------------------------------------------------ #
    # VQA                                                                  #
    # ------------------------------------------------------------------ #

    def vqa(
        self,
        question: str,
        images: Optional[List[Image.Image]] = None,
        **kwargs: Any,
    ) -> str:
        """Visual question answering.

        Parameters
        ----------
        question:
            Natural-language question.
        images:
            Reference images.

        Returns
        -------
        str
            Model answer.

        Example::

            answer = tp.vqa("What colour is the car?", images=[Image.open("car.jpg")])
        """
        self._require_model()
        prompt = build_vqa_prompt(question)
        return self._model.generate(prompt, images=images, **kwargs)

    # ------------------------------------------------------------------ #
    # prompt enhancement                                                   #
    # ------------------------------------------------------------------ #

    def enhance_prompt(
        self,
        prompt: str,
        image: Optional[Image.Image] = None,
        **kwargs: Any,
    ) -> str:
        """Rewrite and enrich *prompt* to be more descriptive.

        Parameters
        ----------
        prompt:
            Original (possibly terse) prompt.
        image:
            Optional reference image to ground the enhancement.

        Returns
        -------
        str
            Enhanced prompt.

        Example::

            better = tp.enhance_prompt("a dog running in the park")
        """
        self._require_model()
        instruction = build_enhancement_prompt(prompt)
        images = [image] if image is not None else None
        return self._model.generate(instruction, images=images, **kwargs)

    # ------------------------------------------------------------------ #
    # video description                                                    #
    # ------------------------------------------------------------------ #

    def describe_video(
        self,
        frames: List[Image.Image],
        focus: str = "action",
        **kwargs: Any,
    ) -> str:
        """Describe a video clip given a list of frames.

        Parameters
        ----------
        frames:
            Ordered list of PIL frames.
        focus:
            ``"action"``, ``"scene"``, ``"emotion"``, or ``"summary"``.

        Returns
        -------
        str
            Video description.

        Example::

            desc = tp.describe_video(frames, focus="summary")
        """
        self._require_model()
        prompt = build_video_description_prompt(focus)
        return self._model.generate(prompt, videos=[frames], **kwargs)

    # ------------------------------------------------------------------ #
    # batch operations                                                     #
    # ------------------------------------------------------------------ #

    def batch_caption(
        self,
        images: List[Image.Image],
        style: str = "brief",
    ) -> List[str]:
        """Caption multiple images in sequence.

        Parameters
        ----------
        images:
            List of PIL images.
        style:
            Caption style.

        Returns
        -------
        List[str]
            One caption per image.

        Example::

            captions = tp.batch_caption([img1, img2, img3], style="tags")
        """
        return [self.caption(img, style=style) for img in images]

    def batch_vqa(
        self,
        question: str,
        images: List[Image.Image],
    ) -> List[str]:
        """Ask the same *question* about each image.

        Parameters
        ----------
        question:
            Question to ask.
        images:
            List of images.

        Returns
        -------
        List[str]
            Answers in the same order as *images*.

        Example::

            answers = tp.batch_vqa("Is there a person?", [img1, img2])
        """
        return [self.vqa(question, images=[img]) for img in images]

    # ------------------------------------------------------------------ #
    # list available styles                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def available_styles() -> List[str]:
        """Return the list of available caption styles.

        Returns
        -------
        List[str]
            Style names.

        Example::

            print(TextProcessor.available_styles())
        """
        return list(STYLE_PROMPTS.keys())
