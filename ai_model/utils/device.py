"""Device detection and resolution utilities.

Provides :class:`DeviceManager` which selects the best available compute
device at runtime and emits helpful log messages.

Usage::

    from ai_model.utils.device import DeviceManager

    dm = DeviceManager("auto")
    device = dm.resolve()   # e.g. "cuda", "mps", or "cpu"
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DeviceManager:
    """Resolve a compute-device string at runtime.

    Parameters
    ----------
    preference:
        ``"auto"``  – pick CUDA → MPS → CPU (default).
        ``"cuda"``  – force CUDA (raises if unavailable).
        ``"mps"``   – force Apple Metal (raises if unavailable).
        ``"cpu"``   – always use the CPU.
        ``"cuda:N"`` – specific CUDA device index.
    """

    def __init__(self, preference: str = "auto") -> None:
        self.preference = preference
        self._resolved: Optional[str] = None

    def resolve(self) -> str:
        """Return the resolved device string, caching the result."""
        if self._resolved is not None:
            return self._resolved
        self._resolved = self._resolve()
        return self._resolved

    def _resolve(self) -> str:
        pref = self.preference.lower()

        if pref == "cpu":
            logger.debug("Device: cpu (forced)")
            return "cpu"

        if pref == "auto":
            return self._auto()

        # explicit device
        try:
            import torch
            device = torch.device(pref)
            if pref.startswith("cuda"):
                if not torch.cuda.is_available():
                    raise RuntimeError("CUDA requested but not available.")
                logger.info("Device: %s (cuda)", pref)
            elif pref == "mps":
                if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
                    raise RuntimeError("MPS requested but not available.")
                logger.info("Device: mps (Apple Metal)")
            return str(device)
        except ImportError:
            logger.warning("torch not installed; falling back to cpu")
            return "cpu"

    def _auto(self) -> str:
        try:
            import torch
            if torch.cuda.is_available():
                dev = "cuda"
                logger.info("Device: cuda (%s)", torch.cuda.get_device_name(0))
                return dev
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                logger.info("Device: mps (Apple Metal)")
                return "mps"
        except ImportError:
            pass
        logger.info("Device: cpu (no GPU detected)")
        return "cpu"

    @staticmethod
    def memory_info() -> dict:
        """Return a best-effort snapshot of memory usage.

        Returns
        -------
        dict
            Keys: ``cuda_allocated_gb``, ``cuda_reserved_gb`` (when CUDA is
            available) and ``ram_used_gb``, ``ram_total_gb`` (always).
        """
        info: dict = {}
        try:
            import torch
            if torch.cuda.is_available():
                info["cuda_allocated_gb"] = torch.cuda.memory_allocated() / 1e9
                info["cuda_reserved_gb"] = torch.cuda.memory_reserved() / 1e9
        except ImportError:
            pass
        try:
            import psutil
            vm = psutil.virtual_memory()
            info["ram_used_gb"] = vm.used / 1e9
            info["ram_total_gb"] = vm.total / 1e9
        except ImportError:
            pass
        return info
