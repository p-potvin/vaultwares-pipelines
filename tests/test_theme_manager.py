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

    def test_hex_to_rgb_valid(self, manager):
        assert manager._hex_to_rgb("#FFFFFF") == (255, 255, 255)
        assert manager._hex_to_rgb("000000") == (0, 0, 0)
        assert manager._hex_to_rgb(" #123456 ") == (18, 52, 86)

    def test_hex_to_rgb_invalid(self, manager):
        with pytest.raises(ValueError):
            manager._hex_to_rgb("#FFF")
        with pytest.raises(ValueError):
            manager._hex_to_rgb("invalid")
        with pytest.raises(ValueError):
            manager._hex_to_rgb("#GGGGGG")

    def test_relative_luminance(self, manager):
        assert manager._relative_luminance((255, 255, 255)) == pytest.approx(1.0)
        assert manager._relative_luminance((0, 0, 0)) == pytest.approx(0.0)
        assert manager._relative_luminance((128, 128, 128)) == pytest.approx(0.21586, abs=1e-4)

    def test_contrast_ratio(self, manager):
        assert manager._contrast_ratio((255, 255, 255), (0, 0, 0)) == 21.0
        assert manager._contrast_ratio((255, 255, 255), (255, 255, 255)) == 1.0

    def test_check_contrast(self, manager):
        res = manager.check_contrast("#FFFFFF", "#000000")
        assert res["ratio"] == 21.0
        assert res["aa_text"] is True
        assert res["aa_large"] is True

        res = manager.check_contrast("#FFFFFF", "#777777")
        assert res["ratio"] == pytest.approx(4.48, abs=0.01)
        assert res["aa_text"] is False
        assert res["aa_large"] is True

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

    def test_get_theme_by_slug(self, manager):
        theme = manager.get_theme_by_slug("vintage-velvet")
        assert theme.name == "Vintage Velvet"
        theme = manager.get_theme_by_slug("  VINTAGE-velvet  ")
        assert theme.name == "Vintage Velvet"
        theme = manager.get_theme_by_slug("non-existent")
        assert theme.name == "Cyberpunk Cinder"

    def test_validate_theme(self, manager):
        valid_theme = VaultTheme("Test", "light", "#FFFFFF", "#000000", "test")
        assert manager.validate_theme(valid_theme) is True
        invalid_mode = VaultTheme("Test", "invalid", "#FFFFFF", "#000000", "test")
        assert manager.validate_theme(invalid_mode) is False
        invalid_primary = VaultTheme("Test", "light", "#FFF", "#000000", "test")
        assert manager.validate_theme(invalid_primary) is False

    def test_export_theme_tokens_light(self, manager):
        theme = manager.get_theme_by_slug("vintage-velvet")
        tokens = manager.export_theme_tokens(theme)
        assert tokens["theme_name"] == "Vintage Velvet"
        assert tokens["mode"] == "light"
        assert tokens["text_primary"] == "#111827"

    def test_export_theme_tokens_dark(self, manager):
        theme = manager.get_theme_by_slug("cyberpunk-cinder")
        tokens = manager.export_theme_tokens(theme)
        assert tokens["theme_name"] == "Cyberpunk Cinder"
        assert tokens["mode"] == "dark"
        assert tokens["text_primary"] == "#F8FAFC"

    def test_export_theme_tokens_invalid_fallback(self, manager):
        invalid_theme = VaultTheme("Test", "invalid", "#FFF", "#000", "test")
        tokens = manager.export_theme_tokens(invalid_theme)
        assert tokens["theme_name"] == "Cyberpunk Cinder"

    def test_get_glass_rgba(self, manager):
        rgba = manager.get_glass_rgba("#FFFFFF", 128)
        assert rgba == "rgba(255, 255, 255, 128)"
