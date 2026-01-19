"""
Color extraction from screenshots and app assets.
Pulls dominant colors to generate matching backgrounds.
"""

from PIL import Image
from colorthief import ColorThief
from typing import List, Tuple, Optional
from pathlib import Path
import colorsys
import io
import re


# Preset color palettes
PRESET_PALETTES = {
    "vibrant": [
        (255, 87, 51),   # Coral red
        (255, 189, 51),  # Golden yellow
        (51, 255, 87),   # Bright green
        (51, 189, 255),  # Sky blue
    ],
    "pastel": [
        (255, 209, 220),  # Pink
        (255, 230, 179),  # Peach
        (179, 230, 255),  # Light blue
        (198, 255, 179),  # Mint
    ],
    "dark": [
        (30, 30, 40),     # Deep navy
        (50, 50, 70),     # Slate
        (80, 60, 90),     # Purple gray
        (40, 60, 80),     # Steel blue
    ],
    "warm": [
        (255, 140, 100),  # Salmon
        (255, 180, 100),  # Peach
        (255, 120, 80),   # Coral
        (255, 200, 150),  # Cream
    ],
    "cool": [
        (100, 180, 255),  # Sky blue
        (150, 200, 255),  # Light blue
        (100, 220, 200),  # Teal
        (180, 220, 255),  # Ice blue
    ],
    "sunset": [
        (255, 150, 100),  # Orange
        (255, 120, 150),  # Pink
        (180, 100, 200),  # Purple
        (100, 80, 160),   # Deep purple
    ],
    "ocean": [
        (200, 230, 245),  # Light blue
        (100, 180, 220),  # Ocean blue
        (60, 140, 180),   # Teal
        (40, 100, 140),   # Deep ocean
    ],
    "forest": [
        (180, 210, 180),  # Sage
        (120, 180, 120),  # Green
        (80, 140, 100),   # Forest
        (60, 100, 80),    # Deep green
    ],
    "berry": [
        (255, 180, 200),  # Light pink
        (220, 100, 150),  # Rose
        (180, 80, 130),   # Berry
        (120, 60, 100),   # Deep plum
    ],
    "monochrome": [
        (240, 240, 245),  # Light gray
        (200, 200, 210),  # Gray
        (150, 150, 160),  # Medium gray
        (100, 100, 110),  # Dark gray
    ],
}


def parse_hex_color(hex_str: str) -> Tuple[int, int, int]:
    """Parse a hex color string to RGB tuple."""
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c * 2 for c in hex_str])
    if len(hex_str) != 6:
        raise ValueError(f"Invalid hex color: {hex_str}")
    return (
        int(hex_str[0:2], 16),
        int(hex_str[2:4], 16),
        int(hex_str[4:6], 16)
    )


def parse_color_string(color_str: str) -> List[Tuple[int, int, int]]:
    """Parse a color string - can be hex codes or preset name."""
    color_str = color_str.strip().lower()

    # Check if it's a preset palette name
    if color_str in PRESET_PALETTES:
        return PRESET_PALETTES[color_str]

    # Otherwise parse as comma-separated hex codes
    colors = []
    for part in color_str.split(','):
        part = part.strip()
        if part:
            colors.append(parse_hex_color(part))

    return colors if colors else PRESET_PALETTES["vibrant"]


def get_available_palettes() -> List[str]:
    """Return list of available preset palette names."""
    return list(PRESET_PALETTES.keys())


def resolve_colors(
    color_arg: Optional[str] = None,
    project_path: Optional[str] = None,
    screenshot_path: Optional[str] = None
) -> List[Tuple[int, int, int]]:
    """
    Resolve colors from various sources.

    Priority:
    1. If color_arg is provided:
       - If it's a preset name (e.g., "sunset"), use that palette
       - If it's hex codes (e.g., "#FF5733,#3498DB"), parse them
    2. If project_path is provided, try to extract from app icon
    3. If screenshot_path is provided, extract from the screenshot
    4. Fall back to "vibrant" preset

    Returns list of RGB tuples.
    """
    # 1. Check explicit color argument
    if color_arg:
        colors = parse_color_string(color_arg)
        if colors:
            return colors

    # 2. Try app icon if project path provided
    if project_path:
        colors = extract_colors_from_app_icon(project_path)
        if colors:
            return colors

    # 3. Try screenshot colors
    if screenshot_path:
        try:
            extractor = ColorExtractor(image_path=screenshot_path)
            return extractor.get_complementary_colors()
        except:
            pass

    # 4. Default fallback
    return PRESET_PALETTES["vibrant"]


def extract_colors_from_app_icon(project_path: str) -> Optional[List[Tuple[int, int, int]]]:
    """
    Extract colors from an iOS app icon in the project.
    Looks for AppIcon in Assets.xcassets or common icon locations.
    """
    project = Path(project_path)

    # Common locations for app icons
    icon_patterns = [
        "**/Assets.xcassets/AppIcon.appiconset/*.png",
        "**/AppIcon.appiconset/*.png",
        "**/Assets.xcassets/AppIcon.imageset/*.png",
        "**/AppIcon*.png",
        "**/Icon*.png",
        "**/icon*.png",
    ]

    icon_path = None
    largest_size = 0

    for pattern in icon_patterns:
        for path in project.glob(pattern):
            if path.is_file():
                try:
                    img = Image.open(path)
                    size = img.size[0] * img.size[1]
                    # Prefer larger icons for better color extraction
                    if size > largest_size:
                        largest_size = size
                        icon_path = path
                except:
                    continue

    if not icon_path:
        return None

    try:
        extractor = ColorExtractor(image_path=str(icon_path))
        return extractor.get_palette(4)
    except:
        return None


class ColorExtractor:
    """Extract and analyze colors from images."""

    def __init__(self, image_path: str = None, image: Image.Image = None):
        self.image_path = image_path
        self.image = image
        self._dominant_color = None
        self._palette = None
    
    def get_dominant_color(self) -> Tuple[int, int, int]:
        """Get the single most dominant color."""
        if self._dominant_color:
            return self._dominant_color
        
        ct = self._get_color_thief()
        self._dominant_color = ct.get_color(quality=1)
        return self._dominant_color
    
    def get_palette(self, color_count: int = 6) -> List[Tuple[int, int, int]]:
        """Get a palette of dominant colors."""
        if self._palette and len(self._palette) >= color_count:
            return self._palette[:color_count]
        
        ct = self._get_color_thief()
        self._palette = ct.get_palette(color_count=color_count, quality=1)
        return self._palette
    
    def get_complementary_colors(self) -> List[Tuple[int, int, int]]:
        """Generate complementary colors for backgrounds."""
        palette = self.get_palette(4)
        complementary = []
        
        for color in palette:
            # Convert to HSV
            r, g, b = [x / 255.0 for x in color]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            
            # Create lighter, desaturated version for backgrounds
            # Reduce saturation, increase value for softer look
            new_s = max(0.1, s * 0.4)
            new_v = min(1.0, v * 1.3 + 0.2)
            
            new_r, new_g, new_b = colorsys.hsv_to_rgb(h, new_s, new_v)
            complementary.append((
                int(new_r * 255),
                int(new_g * 255),
                int(new_b * 255)
            ))
        
        return complementary
    
    def get_background_gradient_colors(self) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """Get two colors suitable for a gradient background."""
        palette = self.get_palette(3)
        
        if len(palette) < 2:
            # Fallback to variations of dominant color
            dominant = self.get_dominant_color()
            return self._lighten_color(dominant, 0.7), self._lighten_color(dominant, 0.9)
        
        # Use two palette colors, lightened for background
        color1 = self._lighten_color(palette[0], 0.6)
        color2 = self._lighten_color(palette[1], 0.8)
        
        return color1, color2
    
    def _lighten_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Lighten a color by mixing with white."""
        r, g, b = color
        return (
            int(r + (255 - r) * factor),
            int(g + (255 - g) * factor),
            int(b + (255 - b) * factor)
        )
    
    def _get_color_thief(self) -> ColorThief:
        """Get ColorThief instance from path or image."""
        if self.image_path:
            return ColorThief(self.image_path)
        elif self.image:
            # Save image to bytes buffer for ColorThief
            buffer = io.BytesIO()
            self.image.save(buffer, format='PNG')
            buffer.seek(0)
            return ColorThief(buffer)
        else:
            raise ValueError("Either image_path or image must be provided")
