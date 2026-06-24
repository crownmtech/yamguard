"""
YamGuard - Color Palette and Theme Configuration
Material Design 3 color system for agricultural AI application
"""

from kivy.utils import get_color_from_hex

# Primary Palette
PRIMARY_GREEN = get_color_from_hex("#16A34A")
DARK_GREEN = get_color_from_hex("#166534")
LIGHT_GREEN = get_color_from_hex("#22C55E")
GREEN_50 = get_color_from_hex("#DCFCE7")
GREEN_100 = get_color_from_hex("#BBF7D0")
GREEN_200 = get_color_from_hex("#86EFAC")
GREEN_300 = get_color_from_hex("#4ADE80")
GREEN_400 = get_color_from_hex("#22C55E")
GREEN_500 = get_color_from_hex("#16A34A")
GREEN_600 = get_color_from_hex("#16A34A")
GREEN_700 = get_color_from_hex("#15803D")
GREEN_800 = get_color_from_hex("#166534")
GREEN_900 = get_color_from_hex("#14532D")

# Status Colors
HEALTHY = get_color_from_hex("#22C55E")
HEALTHY_LIGHT = get_color_from_hex("#DCFCE7")
WARNING = get_color_from_hex("#F59E0B")
WARNING_LIGHT = get_color_from_hex("#FEF3C7")
INFECTED = get_color_from_hex("#DC2626")
INFECTED_LIGHT = get_color_from_hex("#FEE2E2")
INFO = get_color_from_hex("#3B82F6")
INFO_LIGHT = get_color_from_hex("#DBEAFE")

# Neutral Colors
BACKGROUND = get_color_from_hex("#F8FAFC")
SURFACE = get_color_from_hex("#FFFFFF")
SURFACE_VARIANT = get_color_from_hex("#F1F5F9")
TEXT_PRIMARY = get_color_from_hex("#1E293B")
TEXT_SECONDARY = get_color_from_hex("#64748B")
TEXT_TERTIARY = get_color_from_hex("#94A3B8")
TEXT_ON_PRIMARY = get_color_from_hex("#FFFFFF")

# Border and Divider Colors
BORDER = get_color_from_hex("#E2E8F0")
DIVIDER = get_color_from_hex("#F1F5F9")

# Chart Colors
CHART_COLORS = [
    get_color_from_hex("#16A34A"),
    get_color_from_hex("#F59E0B"),
    get_color_from_hex("#DC2626"),
    get_color_from_hex("#3B82F6"),
    get_color_from_hex("#8B5CF6"),
    get_color_from_hex("#EC4899"),
    get_color_from_hex("#06B6D4"),
]

# Spectral Band Colors (for hyperspectral visualization)
SPECTRAL_COLORS = {
    "violet": get_color_from_hex("#8B5CF6"),
    "blue": get_color_from_hex("#3B82F6"),
    "green": get_color_from_hex("#22C55E"),
    "yellow": get_color_from_hex("#F59E0B"),
    "red": get_color_from_hex("#EF4444"),
    "nir": get_color_from_hex("#DC2626"),
    "swir": get_color_from_hex("#7C2D12"),
}

# Elevation Shadows (rgba)
SHADOW_SM = (0, 0, 0, 0.05)
SHADOW_MD = (0, 0, 0, 0.1)
SHADOW_LG = (0, 0, 0, 0.15)
SHADOW_XL = (0, 0, 0, 0.2)

# Gradient Presets (start_color, end_color)
GRADIENT_PRIMARY = (PRIMARY_GREEN, DARK_GREEN)
GRADIENT_HEALTHY = (LIGHT_GREEN, PRIMARY_GREEN)
GRADIENT_WARNING = (get_color_from_hex("#FBBF24"), WARNING)
GRADIENT_INFECTED = (get_color_from_hex("#EF4444"), INFECTED)

# Ripple Effect Colors
RIPPLE_GREEN = (*PRIMARY_GREEN[:3], 0.3)
RIPPLE_RED = (*INFECTED[:3], 0.3)
