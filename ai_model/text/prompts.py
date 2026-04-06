"""
Prompt engineering utilities for SmolVLM2 and compatible models.

Provides reusable :class:`PromptTemplate` objects and factory functions that
produce well-formed prompts for common multi-modal tasks.

Usage::

    from ai_model.text.prompts import build_caption_prompt, PromptTemplate

    prompt = build_caption_prompt(style="detailed")
    custom = PromptTemplate(
        template="Translate the following into {language}: {text}",
        description="Simple translation template",
    )
    print(custom.format(language="French", text="Hello world"))
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


# --------------------------------------------------------------------------- #
# PromptTemplate                                                               #
# --------------------------------------------------------------------------- #

@dataclass
class PromptTemplate:
    """A simple string template with named placeholders.

    Attributes
    ----------
    template:
        Template string with ``{placeholder}`` variables.
    description:
        Human-readable description of what this template does.

    Example::

        t = PromptTemplate(
            template="Describe the {subject} in {style} terms.",
            description="Flexible description template",
        )
        print(t.format(subject="landscape", style="poetic"))
    """

    template: str
    description: str = ""

    def format(self, **kwargs) -> str:
        """Substitute *kwargs* into the template.

        Parameters
        ----------
        **kwargs:
            Named values for each placeholder in the template.

        Returns
        -------
        str
            Filled template string.
        """
        return self.template.format(**kwargs)

    def __str__(self) -> str:
        return self.template


# --------------------------------------------------------------------------- #
# built-in style prompts                                                       #
# --------------------------------------------------------------------------- #

STYLE_PROMPTS: Dict[str, str] = {
    "brief": "Describe this image in one sentence.",
    "detailed": (
        "Provide a detailed description of this image. "
        "Include all visible objects, their colours, spatial relationships, "
        "lighting conditions, and any text or symbols present."
    ),
    "tags": (
        "List the main subjects, objects, styles, and attributes in this image "
        "as a comma-separated list of keywords. No sentences."
    ),
    "cinematic": (
        "Describe this image as a film director would describe a shot. "
        "Include composition, lighting, mood, camera angle, and focal length hints."
    ),
    "sd_prompt": (
        "Convert this image into a Stable Diffusion positive prompt. "
        "Use descriptive comma-separated phrases, include art style, lighting, "
        "and quality modifiers. Do not include negative prompts."
    ),
}


# --------------------------------------------------------------------------- #
# factory functions                                                            #
# --------------------------------------------------------------------------- #

def build_caption_prompt(style: str = "detailed") -> str:
    """Return the caption prompt for the given *style*.

    Parameters
    ----------
    style:
        One of ``"brief"``, ``"detailed"``, ``"tags"``, ``"cinematic"``,
        ``"sd_prompt"``.

    Returns
    -------
    str
        Ready-to-use prompt string.

    Example::

        prompt = build_caption_prompt("cinematic")
        caption = model.generate(prompt, images=[img])
    """
    if style not in STYLE_PROMPTS:
        raise ValueError(f"Unknown style {style!r}. Choose from {list(STYLE_PROMPTS)}")
    return STYLE_PROMPTS[style]


def build_vqa_prompt(question: str) -> str:
    """Wrap *question* in a VQA-style template.

    Parameters
    ----------
    question:
        The natural-language question.

    Returns
    -------
    str
        Formatted prompt.

    Example::

        prompt = build_vqa_prompt("How many cars are in the image?")
    """
    return f"Look at this image carefully and answer the following question: {question}"


def build_enhancement_prompt(original_prompt: str) -> str:
    """Prompt instructing the model to enrich *original_prompt*.

    Parameters
    ----------
    original_prompt:
        The terse or incomplete prompt to enhance.

    Returns
    -------
    str
        Enhancement instruction.

    Example::

        enhanced = model.generate(
            build_enhancement_prompt("a cat sleeping"),
            images=[ref_image],
        )
    """
    return (
        f'Rewrite and significantly expand the following image-generation prompt '
        f'to be more descriptive, vivid, and detailed while preserving its intent.  '
        f'Return only the improved prompt without any explanation or commentary.\n\n'
        f'Original prompt: "{original_prompt}"'
    )


def build_video_description_prompt(focus: str = "action") -> str:
    """Return a video description prompt with a specific *focus*.

    Parameters
    ----------
    focus:
        ``"action"``  – describe what is happening.
        ``"scene"``   – describe the visual environment.
        ``"emotion"`` – describe the mood and emotional tone.
        ``"summary"`` – brief one-sentence summary.

    Returns
    -------
    str
        Formatted prompt.

    Example::

        prompt = build_video_description_prompt("scene")
        description = model.generate(prompt, videos=[frames])
    """
    focus_map = {
        "action": "Describe in detail what is happening in this video clip.",
        "scene": (
            "Describe the visual environment, setting, and background "
            "shown in this video clip."
        ),
        "emotion": (
            "Describe the mood, atmosphere, and emotional tone conveyed "
            "by this video clip."
        ),
        "summary": "Summarise this video clip in a single sentence.",
    }
    if focus not in focus_map:
        raise ValueError(f"Unknown focus {focus!r}. Choose from {list(focus_map)}")
    return focus_map[focus]
