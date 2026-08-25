 """
WebScraper Pro - Design System & Styles
Centralized color palette, typography, and component styling for a professional commercial look.
"""

import customtkinter as ctk


# ============================================================
# COLOR PALETTE
# ============================================================

class Colors:
    """Primary color palette - Modern blue/dark theme."""
    # Background
    BG_DARK = "#0D1117"
    BG_MAIN = "#161B22"
    BG_CARD = "#1C2128"
    BG_ELEVATED = "#21262D"
    BG_INPUT = "#0D1117"
    BG_SIDEBAR = "#0D1117"
    BG_HOVER = "#262C36"
    BG_ACTIVE = "#2D333B"
    BG_SELECTED = "#1F3A5F"

    # Text
    TEXT_PRIMARY = "#E6EDF3"
    TEXT_SECONDARY = "#8B949E"
    TEXT_MUTED = "#6E7681"
    TEXT_INVERSE = "#FFFFFF"
    TEXT_LINK = "#58A6FF"
    TEXT_SUCCESS = "#3FB950"
    TEXT_WARNING = "#D29922"
    TEXT_ERROR = "#F85149"

    # Brand
    BRAND_PRIMARY = "#2F81F7"
    BRAND_PRIMARY_HOVER = "#58A6FF"
    BRAND_PRIMARY_DARK = "#1F6FEB"
    BRAND_ACCENT = "#A371F7"
    BRAND_ACCENT_HOVER = "#BC8CFF"

    # Status
    SUCCESS = "#238636"
    SUCCESS_BG = "#0F2D1A"
    WARNING = "#9E6A03"
    WARNING_BG = "#2D2000"
    ERROR = "#DA3633"
    ERROR_BG = "#2D0B0B"
    INFO = "#2F81F7"
    INFO_BG = "#0C2D6B"

    # Borders
    BORDER = "#30363D"
    BORDER_LIGHT = "#21262D"
    BORDER_FOCUS = "#2F81F7"

    # Misc
    SCROLLBAR = "#30363D"
    SCROLLBAR_HOVER = "#484F58"
    SHADOW = "#00000040"


class LightColors:
    """Light theme color palette."""
    BG_DARK = "#F6F8FA"
    BG_MAIN = "#FFFFFF"
    BG_CARD = "#FFFFFF"
    BG_ELEVATED = "#F6F8FA"
    BG_INPUT = "#FFFFFF"
    BG_SIDEBAR = "#F6F8FA"
    BG_HOVER = "#EBEEF1"
    BG_ACTIVE = "#DFE2E5"
    BG_SELECTED = "#DBEAFE"

    TEXT_PRIMARY = "#1F2328"
    TEXT_SECONDARY = "#656D76"
    TEXT_MUTED = "#8B949E"
    TEXT_INVERSE = "#FFFFFF"
    TEXT_LINK = "#0969DA"
    TEXT_SUCCESS = "#1A7F37"
    TEXT_WARNING = "#9A6700"
    TEXT_ERROR = "#D1242F"

    BRAND_PRIMARY = "#0969DA"
    BRAND_PRIMARY_HOVER = "#0550AE"
    BRAND_PRIMARY_DARK = "#0349B4"
    BRAND_ACCENT = "#8250DF"
    BRAND_ACCENT_HOVER = "#6E40C9"

    SUCCESS = "#1A7F37"
    SUCCESS_BG = "#DAFBE1"
    WARNING = "#9A6700"
    WARNING_BG = "#FFF8C5"
    ERROR = "#D1242F"
    ERROR_BG = "#FFE1E1"
    INFO = "#0969DA"
    INFO_BG = "#DDF4FF"

    BORDER = "#D0D7DE"
    BORDER_LIGHT = "#EBEEF1"
    BORDER_FOCUS = "#0969DA"

    SCROLLBAR = "#D0D7DE"
    SCROLLBAR_HOVER = "#AFB8C1"
    SHADOW = "#00000015"


# ============================================================
# TYPOGRAPHY
# ============================================================

class Typography:
    FONT_FAMILY = "Segoe UI"
    HEADING_FONT = "Segoe UI Semibold"
    MONO_FONT = "Cascadia Code"

    H1_SIZE = 24
    H2_SIZE = 18
    H3_SIZE = 14
    BODY_SIZE = 13
    SMALL_SIZE = 11
    TINY_SIZE = 10


class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
    XXXL = 32


class Radius:
    SM = 4
    MD = 6
    LG = 8
    XL = 12
    FULL = 20


# ============================================================
# THEME MANAGER
# ============================================================

class ThemeManager:
    """Manages application theme switching."""

    def __init__(self):
        self._is_dark = True
        self._colors = Colors

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    @property
    def colors(self):
        return self._colors

    def toggle(self):
        self._is_dark = not self._is_dark
        self._colors = Colors if self._is_dark else LightColors
        self.apply_ctk_theme()

    def set_dark(self):
        if not self._is_dark:
            self._is_dark = True
            self._colors = Colors
            self.apply_ctk_theme()

    def set_light(self):
        if self._is_dark:
            self._is_dark = False
            self._colors = LightColors
            self.apply_ctk_theme()

    def apply_ctk_theme(self):
        if self._is_dark:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")


# Global theme instance
theme = ThemeManager()


def apply_custom_styles():
    """Apply custom widget styling after theme change."""
    c = theme.colors
    ctk.set_default_color_theme("blue")
