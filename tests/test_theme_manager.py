import pytest
from importlib import import_module

# Handling the hyphen in the directory name
theme_manager_mod = import_module("vault-themes.theme_manager")
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
        # Mid gray #808080 (128, 128, 128)
        # channel_to_linear(128) -> c = 128/255 = 0.50196
        # c > 0.03928 -> ((c + 0.055) / 1.055) ** 2.4
        # ((0.50196 + 0.055) / 1.055) ** 2.4 = (0.55696 / 1.055) ** 2.4 = 0.52792 ** 2.4 = 0.21586
        # luminance = 0.2126 * 0.21586 + 0.7152 * 0.21586 + 0.0722 * 0.21586 = 0.21586
        assert manager._relative_luminance((128, 128, 128)) == pytest.approx(0.21586, abs=1e-4)

    def test_contrast_ratio(self, manager):
        # White and Black
        assert manager._contrast_ratio((255, 255, 255), (0, 0, 0)) == 21.0
        # Same color
        assert manager._contrast_ratio((255, 255, 255), (255, 255, 255)) == 1.0

    def test_check_contrast(self, manager):
        # High contrast
        res = manager.check_contrast("#FFFFFF", "#000000")
        assert res["ratio"] == 21.0
        assert res["aa_text"] is True
        assert res["aa_large"] is True

        # Low contrast (e.g., #777777 on #FFFFFF)
        # White lum = 1.0
        # #777777 is (119, 119, 119). c = 119/255 = 0.4666
        # ((0.4666+0.055)/1.055)**2.4 = (0.5216/1.055)**2.4 = 0.4944**2.4 = 0.184
        # ratio = (1.0 + 0.05) / (0.1841 + 0.05) = 1.05 / 0.2341 = 4.485... -> 4.48
        res = manager.check_contrast("#FFFFFF", "#777777")
        assert res["ratio"] == 4.48
        assert res["aa_text"] is False # Threshold is 4.5
        assert res["aa_large"] is True  # Threshold is 3.0

    def test_get_themes(self, manager):
        themes = manager.get_themes()
        assert len(themes) == 9
        assert isinstance(themes[0], VaultTheme)

    def test_get_theme_by_index(self, manager):
        # Valid index
        theme = manager.get_theme(0)
        assert theme.name == "Vintage Velvet"

        # Out of bounds
        theme = manager.get_theme(99)
        assert theme.name == "Cyberpunk Cinder" # Default index 1

        # Negative index
        theme = manager.get_theme(-1)
        assert theme.name == "Cyberpunk Cinder" # Default index 1

    def test_get_theme_by_slug(self, manager):
        # Valid slug
        theme = manager.get_theme_by_slug("vintage-velvet")
        assert theme.name == "Vintage Velvet"

        # Case insensitive and whitespace
        theme = manager.get_theme_by_slug("  VINTAGE-velvet  ")
        assert theme.name == "Vintage Velvet"

        # Non-existent slug
        theme = manager.get_theme_by_slug("non-existent")
        assert theme.name == "Cyberpunk Cinder" # Default index 1

    def test_validate_theme(self, manager):
        valid_theme = VaultTheme("Test", "light", "#FFFFFF", "#000000", "test")
        assert manager.validate_theme(valid_theme) is True

        invalid_mode = VaultTheme("Test", "invalid", "#FFFFFF", "#000000", "test")
        assert manager.validate_theme(invalid_mode) is False

        invalid_primary = VaultTheme("Test", "light", "#FFF", "#000000", "test")
        assert manager.validate_theme(invalid_primary) is False

        invalid_accent = VaultTheme("Test", "light", "#FFFFFF", "not-a-color", "test")
        assert manager.validate_theme(invalid_accent) is False

    def test_export_theme_tokens_light(self, manager):
        theme = manager.get_theme_by_slug("vintage-velvet") # light
        tokens = manager.export_theme_tokens(theme)

        assert tokens["theme_name"] == "Vintage Velvet"
        assert tokens["mode"] == "light"
        assert tokens["background"] == "#F5F5DC"
        assert tokens["text_primary"] == "#111827"
        assert "surface" in tokens
        assert "accent_hover" in tokens
        assert tokens["success"] == "#16A34A"

    def test_export_theme_tokens_dark(self, manager):
        theme = manager.get_theme_by_slug("cyberpunk-cinder") # dark
        tokens = manager.export_theme_tokens(theme)

        assert tokens["theme_name"] == "Cyberpunk Cinder"
        assert tokens["mode"] == "dark"
        assert tokens["text_primary"] == "#F8FAFC"
        assert "surface" in tokens
        assert "accent_hover" in tokens

    def test_export_theme_tokens_invalid_fallback(self, manager):
        invalid_theme = VaultTheme("Test", "invalid", "#FFF", "#000", "test")
        tokens = manager.export_theme_tokens(invalid_theme)
        # Should fallback to Cyberpunk Cinder (index 1)
        assert tokens["theme_name"] == "Cyberpunk Cinder"

    def test_get_glass_rgba(self, manager):
        rgba = manager.get_glass_rgba("#FFFFFF", 128)
        assert rgba == "rgba(255, 255, 255, 128)"

        rgba = manager.get_glass_rgba("000000", 255)
        assert rgba == "rgba(0, 0, 0, 255)"
