"""Tests for core configuration and device management."""

import pytest
from ai_model.core.config import ModelConfig
from ai_model.utils.device import DeviceManager


class TestModelConfig:
    def test_defaults(self):
        cfg = ModelConfig()
        assert cfg.model_id == "HuggingFaceTB/SmolVLM2-500M-Video-Instruct"
        assert cfg.device == "auto"
        assert cfg.dtype == "float32"
        assert cfg.max_new_tokens == 256

    def test_generation_kwargs_no_sample(self):
        cfg = ModelConfig(max_new_tokens=128)
        kwargs = cfg.generation_kwargs()
        assert kwargs["max_new_tokens"] == 128
        assert "do_sample" not in kwargs

    def test_generation_kwargs_sample(self):
        cfg = ModelConfig(do_sample=True, temperature=0.7, top_p=0.9)
        kwargs = cfg.generation_kwargs()
        assert kwargs["do_sample"] is True
        assert kwargs["temperature"] == 0.7
        assert kwargs["top_p"] == 0.9

    def test_custom_fields(self):
        cfg = ModelConfig(model_id="my-model", device="cpu", low_memory=True)
        assert cfg.model_id == "my-model"
        assert cfg.device == "cpu"
        assert cfg.low_memory is True


class TestDeviceManager:
    def test_cpu(self):
        dm = DeviceManager("cpu")
        assert dm.resolve() == "cpu"

    def test_cached(self):
        dm = DeviceManager("cpu")
        d1 = dm.resolve()
        d2 = dm.resolve()
        assert d1 == d2

    def test_auto_returns_string(self):
        dm = DeviceManager("auto")
        device = dm.resolve()
        assert isinstance(device, str)
        assert device in ("cpu", "cuda", "mps") or device.startswith("cuda:")

    def test_memory_info_returns_dict(self):
        info = DeviceManager.memory_info()
        assert isinstance(info, dict)
