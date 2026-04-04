"""
High-level :class:`ImageProcessor` that bundles all image operations into
a single, chainable, model-aware interface.

Usage (standalone – no ML model)::

    from smolvlm2_wrapper.image.processor import ImageProcessor
    from PIL import Image

    proc = ImageProcessor()
    result = (
        proc.load("photo.jpg")
            .resize(640, 480)
            .sharpen(percent=150)
            .save("output/result.jpg")
    )

Usage (with SmolVLM2 for captioning / guided inpainting)::

    from smolvlm2_wrapper import SmolVLM2Wrapper, ImageProcessor

    model = SmolVLM2Wrapper()
    proc  = ImageProcessor(model=model)
    caption = proc.load("photo.jpg").caption()
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Tuple, Union

from PIL import Image

from smolvlm2_wrapper.image import manipulation, mask as mask_mod, inpaint as inpaint_mod

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Chainable image processing pipeline with optional model integration.

    Parameters
    ----------
    model:
        Optional :class:`~smolvlm2_wrapper.core.model.BaseModelWrapper`
        instance.  When provided, methods such as :meth:`caption` and
        :meth:`guided_inpaint` delegate to the model.
    """

    def __init__(self, model=None) -> None:
        self._model = model
        self._image: Optional[Image.Image] = None

    # ------------------------------------------------------------------ #
    # state management                                                     #
    # ------------------------------------------------------------------ #

    def load(self, source: Union[str, Path, Image.Image]) -> "ImageProcessor":
        """Load an image from file or PIL object.

        Parameters
        ----------
        source:
            File path or PIL image.

        Returns
        -------
        ImageProcessor
            Self (for chaining).
        """
        from smolvlm2_wrapper.utils.io import load_image
        self._image = load_image(source)
        return self

    def set_image(self, image: Image.Image) -> "ImageProcessor":
        """Set the current image directly.

        Parameters
        ----------
        image:
            PIL image.

        Returns
        -------
        ImageProcessor
            Self (for chaining).
        """
        self._image = image.convert("RGB")
        return self

    def get_image(self) -> Image.Image:
        """Return the current image.

        Raises
        ------
        RuntimeError
            If no image has been loaded yet.
        """
        if self._image is None:
            raise RuntimeError("No image loaded.  Call load() or set_image() first.")
        return self._image

    def save(self, dest: Union[str, Path]) -> Path:
        """Save the current image to *dest* and return the absolute path.

        Parameters
        ----------
        dest:
            Destination file path.

        Returns
        -------
        pathlib.Path
            Absolute path to saved file.
        """
        from smolvlm2_wrapper.utils.io import save_image
        return save_image(self.get_image(), dest)

    def clone(self) -> "ImageProcessor":
        """Return a new processor with a copy of the current image."""
        p = ImageProcessor(model=self._model)
        if self._image is not None:
            p._image = self._image.copy()
        return p

    # ------------------------------------------------------------------ #
    # manipulation – each returns self for chaining                       #
    # ------------------------------------------------------------------ #

    def resize(self, width: int, height: int) -> "ImageProcessor":
        """Resize to *width* × *height*.

        Example::

            proc.load("photo.jpg").resize(320, 240).save("small.jpg")
        """
        self._image = manipulation.resize(self.get_image(), width, height)
        return self

    def crop(self, left: int, top: int, right: int, bottom: int) -> "ImageProcessor":
        """Crop to the specified box.

        Example::

            proc.load("photo.jpg").crop(0, 0, 200, 200).save("top_left.jpg")
        """
        self._image = manipulation.crop(self.get_image(), left, top, right, bottom)
        return self

    def rotate(self, angle: float, expand: bool = True) -> "ImageProcessor":
        """Rotate counter-clockwise by *angle* degrees.

        Example::

            proc.load("photo.jpg").rotate(90).save("rotated.jpg")
        """
        self._image = manipulation.rotate(self.get_image(), angle, expand=expand)
        return self

    def flip(self, direction: str = "horizontal") -> "ImageProcessor":
        """Flip horizontally or vertically.

        Example::

            proc.load("photo.jpg").flip("vertical").save("flipped.jpg")
        """
        self._image = manipulation.flip(self.get_image(), direction)
        return self

    def sharpen(self, radius: float = 2.0, percent: int = 150) -> "ImageProcessor":
        """Sharpen using unsharp mask.

        Example::

            proc.load("photo.jpg").sharpen(percent=200).save("sharp.jpg")
        """
        self._image = manipulation.sharpen(self.get_image(), radius=radius, percent=percent)
        return self

    def blur(self, radius: float = 2.0) -> "ImageProcessor":
        """Apply Gaussian blur.

        Example::

            proc.load("photo.jpg").blur(radius=5).save("soft.jpg")
        """
        self._image = manipulation.blur(self.get_image(), radius=radius)
        return self

    def adjust_brightness(self, factor: float) -> "ImageProcessor":
        """Adjust brightness.  factor=1.0 is unchanged.

        Example::

            proc.load("photo.jpg").adjust_brightness(1.5).save("bright.jpg")
        """
        self._image = manipulation.adjust_brightness(self.get_image(), factor)
        return self

    def adjust_contrast(self, factor: float) -> "ImageProcessor":
        """Adjust contrast.  factor=1.0 is unchanged.

        Example::

            proc.load("photo.jpg").adjust_contrast(1.3).save("contrast.jpg")
        """
        self._image = manipulation.adjust_contrast(self.get_image(), factor)
        return self

    def adjust_saturation(self, factor: float) -> "ImageProcessor":
        """Adjust saturation.  0.0 = greyscale, 1.0 = unchanged.

        Example::

            proc.load("photo.jpg").adjust_saturation(0).save("grey.jpg")
        """
        self._image = manipulation.adjust_saturation(self.get_image(), factor)
        return self

    def apply_filter(self, name: str) -> "ImageProcessor":
        """Apply a named convolution filter.

        Available: ``"edge_enhance"``, ``"emboss"``, ``"find_edges"``,
        ``"smooth"``, ``"detail"``, ``"contour"``.

        Example::

            proc.load("photo.jpg").apply_filter("emboss").save("emboss.jpg")
        """
        self._image = manipulation.apply_filter(self.get_image(), name)
        return self

    def upscale(self, scale: int = 2) -> "ImageProcessor":
        """Upscale by integer *scale* factor.

        Example::

            proc.load("photo.jpg").upscale(2).save("2x.jpg")
        """
        self._image = manipulation.upscale(self.get_image(), scale)
        return self

    def convert(self, mode: str) -> "ImageProcessor":
        """Convert to a different PIL colour mode.

        Example::

            proc.load("photo.jpg").convert("L").save("grey.jpg")
        """
        self._image = manipulation.convert_color_space(self.get_image(), mode)
        return self

    def add_noise(self, std: float = 15.0, seed: Optional[int] = None) -> "ImageProcessor":
        """Add Gaussian noise.

        Example::

            proc.load("photo.jpg").add_noise(std=10).save("noisy.jpg")
        """
        self._image = manipulation.add_noise(self.get_image(), std=std, seed=seed)
        return self

    def denoise(self, size: int = 3) -> "ImageProcessor":
        """Remove noise using median filter.

        Example::

            proc.load("photo.jpg").denoise(size=5).save("clean.jpg")
        """
        self._image = manipulation.denoise(self.get_image(), size=size)
        return self

    # ------------------------------------------------------------------ #
    # masking                                                              #
    # ------------------------------------------------------------------ #

    def apply_mask(
        self,
        mask: Image.Image,
        background: Union[Tuple[int, int, int], Image.Image] = (0, 0, 0),
    ) -> "ImageProcessor":
        """Composite the current image through *mask*.

        Parameters
        ----------
        mask:
            ``"L"`` mode mask (white = keep, black = use background).
        background:
            Background colour tuple or PIL image.

        Example::

            from smolvlm2_wrapper.image.mask import create_rect_mask
            mask = create_rect_mask(w, h, (100, 100, 300, 300))
            proc.load("photo.jpg").apply_mask(mask).save("masked.jpg")
        """
        self._image = mask_mod.apply_mask(self.get_image(), mask, background)
        return self

    # ------------------------------------------------------------------ #
    # inpainting / healing                                                 #
    # ------------------------------------------------------------------ #

    def inpaint(self, mask: Image.Image) -> "ImageProcessor":
        """Fill the masked region using context from surrounding pixels.

        Parameters
        ----------
        mask:
            White = region to fill.

        Example::

            proc.load("photo.jpg").inpaint(mask).save("inpainted.jpg")
        """
        self._image = inpaint_mod.inpaint(self.get_image(), mask, model=self._model)
        return self

    def outpaint(
        self,
        padding: Tuple[int, int, int, int],
        fill_color: Tuple[int, int, int] = (128, 128, 128),
    ) -> "ImageProcessor":
        """Extend the canvas.

        Parameters
        ----------
        padding:
            ``(top, right, bottom, left)`` in pixels.
        fill_color:
            Background seed colour.

        Example::

            proc.load("photo.jpg").outpaint((0, 100, 0, 100)).save("wide.jpg")
        """
        self._image = inpaint_mod.outpaint(self.get_image(), padding, fill_color, model=self._model)
        return self

    def heal(self, mask: Image.Image, patch_size: int = 16) -> "ImageProcessor":
        """Remove objects / blemishes in the masked area via patch matching.

        Parameters
        ----------
        mask:
            White = region to heal.
        patch_size:
            Patch side length in pixels.

        Example::

            proc.load("photo.jpg").heal(watermark_mask).save("healed.jpg")
        """
        self._image = inpaint_mod.heal(self.get_image(), mask, patch_size=patch_size)
        return self

    # ------------------------------------------------------------------ #
    # model-powered operations                                             #
    # ------------------------------------------------------------------ #

    def caption(self, style: str = "detailed") -> str:
        """Generate a caption for the current image using the attached model.

        Parameters
        ----------
        style:
            ``"brief"``, ``"detailed"``, or ``"tags"``.

        Returns
        -------
        str
            Caption text.

        Raises
        ------
        RuntimeError
            If no model was provided at construction.

        Example::

            from smolvlm2_wrapper import SmolVLM2Wrapper, ImageProcessor
            proc = ImageProcessor(model=SmolVLM2Wrapper())
            caption = proc.load("photo.jpg").caption()
        """
        if self._model is None:
            raise RuntimeError("No model attached.  Pass model=SmolVLM2Wrapper() to ImageProcessor.")
        return self._model.caption(self.get_image(), style=style)

    def describe(self, question: str = "Describe this image in detail.") -> str:
        """Ask an arbitrary question about the current image.

        Parameters
        ----------
        question:
            Any natural-language instruction or question.

        Returns
        -------
        str
            Model response.

        Example::

            answer = proc.load("chart.png").describe("What does this chart show?")
        """
        if self._model is None:
            raise RuntimeError("No model attached.")
        return self._model.answer_question(question, images=[self.get_image()])

    def enhance_prompt(self, prompt: str) -> str:
        """Use the model to enrich *prompt* using the current image as context.

        Parameters
        ----------
        prompt:
            Base prompt to enhance.

        Returns
        -------
        str
            Enhanced prompt.

        Example::

            better = proc.load("photo.jpg").enhance_prompt("a beach scene")
        """
        if self._model is None:
            raise RuntimeError("No model attached.")
        return self._model.enhance_prompt(prompt, image=self.get_image())
