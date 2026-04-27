import pytest
import os
import importlib.util

# Robustly load the module from the hyphenated directory
module_name = "theme_manager"
file_path = os.path.join(os.getcwd(), "vault-themes", "theme_manager.py")
spec = importlib.util.spec_from_file_location(module_name, file_path)
theme_manager_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme_manager_mod)

VaultThemeManager = theme_manager_mod.VaultThemeManager
VaultTheme = theme_manager_mod.VaultTheme

class TestVaultThemeManager:
    @pytest.fixture
    def manager(self):
        return VaultThemeManager()

    def test_get_themes(self, manager):
        themes = manager.get_themes()
        assert len(themes) == 9
        assert isinstance(themes[0], VaultTheme)

    def test_get_theme_by_index(self, manager):
        theme = manager.get_theme(0)
        assert theme.name == "Vintage Velvet"
        theme = manager.get_theme(99)
        assert theme.name == "Cyberpunk Cinder"
        theme = manager.get_theme(-1)
        assert theme.name == "Cyberpunk Cinder"

    def test_get_glass_rgba(self, manager):
        rgba = manager.get_glass_rgba("#FFFFFF", 128)
        assert rgba == "rgba(255, 255, 255, 128)"
