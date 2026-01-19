"""
Device frame management for mockups.
Handles loading device frames and compositing screenshots into them.
"""

from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class DeviceSpec:
    """Specification for a device frame."""
    name: str
    frame_path: Optional[str]  # Path to PNG frame (relative to assets/frames/)
    screen_size: Tuple[int, int]  # Width, Height of the screen area in the frame
    screen_offset: Tuple[int, int]  # X, Y offset from frame top-left to screen top-left
    corner_radius: int
    frame_color: Tuple[int, int, int, int]  # RGBA for procedural frame fallback


# Default assets directory
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets" / "frames"


# iPhone 15 Pro Max - for use with real PNG frame
# Screen coordinates are for the webmobilefirst.com mockup (938x1926 frame)
IPHONE_15_PRO_MAX = DeviceSpec(
    name="iPhone 15 Pro Max",
    frame_path="iphone_15_pro_max.png",
    screen_size=(862, 1868),  # Screen area within the frame
    screen_offset=(38, 29),   # Offset to screen top-left corner
    corner_radius=100,
    frame_color=(30, 30, 35, 255)
)

# iPhone 16 Pro Max - for use with real PNG frame
IPHONE_16_PRO_MAX = DeviceSpec(
    name="iPhone 16 Pro Max",
    frame_path="iphone_16_pro_max.png",
    screen_size=(862, 1868),
    screen_offset=(38, 29),
    corner_radius=100,
    frame_color=(20, 20, 25, 255)  # Darker titanium
)

# iPhone 17 Pro Max specifications (estimated, procedural fallback)
IPHONE_17_PRO_MAX = DeviceSpec(
    name="iPhone 17 Pro Max",
    frame_path="iphone_17_pro_max.png",  # Will use if available, else procedural
    screen_size=(1320, 2868),
    screen_offset=(48, 48),
    corner_radius=140,
    frame_color=(30, 30, 35, 255)
)

# Device catalog
DEVICE_CATALOG = {
    "iphone_15_pro_max": IPHONE_15_PRO_MAX,
    "iphone_16_pro_max": IPHONE_16_PRO_MAX,
    "iphone_17_pro_max": IPHONE_17_PRO_MAX,
}


class DeviceFrame:
    """Handles device frame rendering and screenshot compositing."""
    
    def __init__(self, device: str = "iphone_17_pro_max", assets_path: str = None):
        self.device_spec = DEVICE_CATALOG.get(device, IPHONE_17_PRO_MAX)
        self.assets_path = Path(assets_path) if assets_path else ASSETS_DIR
        self._frame_image = None
        self._using_png_frame = False

    def get_frame(self) -> Image.Image:
        """Get or generate the device frame."""
        if self._frame_image:
            return self._frame_image.copy()

        # Check for PNG frame asset
        if self.device_spec.frame_path:
            frame_file = self.assets_path / self.device_spec.frame_path
            if frame_file.exists():
                print(f"Loading device frame: {frame_file}")
                self._frame_image = Image.open(frame_file).convert('RGBA')
                self._using_png_frame = True
                return self._frame_image.copy()

        # Generate procedural frame as fallback
        print("Using procedural device frame (no PNG found)")
        self._frame_image = self._generate_frame()
        self._using_png_frame = False
        return self._frame_image.copy()

    @property
    def using_png_frame(self) -> bool:
        """Check if using a real PNG frame vs procedural."""
        return self._using_png_frame
    
    def composite_screenshot(self, screenshot: Image.Image, 
                            add_shadow: bool = True,
                            shadow_offset: Tuple[int, int] = (30, 40),
                            shadow_blur: int = 60) -> Image.Image:
        """
        Place a screenshot into the device frame.
        
        Args:
            screenshot: The screenshot to place in the device
            add_shadow: Whether to add a drop shadow
            shadow_offset: X, Y offset for shadow
            shadow_blur: Blur radius for shadow
        
        Returns:
            Device mockup with screenshot composited
        """
        frame = self.get_frame()
        spec = self.device_spec
        
        # Resize screenshot to fit screen area
        screenshot_resized = screenshot.resize(spec.screen_size, Image.Resampling.LANCZOS)
        
        # Apply corner radius mask to screenshot
        screenshot_masked = self._apply_corner_mask(screenshot_resized, spec.corner_radius - 10)
        
        # Composite screenshot into frame
        frame.paste(screenshot_masked, spec.screen_offset, screenshot_masked)
        
        if add_shadow:
            frame = self._add_shadow(frame, shadow_offset, shadow_blur)
        
        return frame
    
    def _generate_frame(self) -> Image.Image:
        """Generate a realistic procedural iPhone device frame."""
        spec = self.device_spec

        # Calculate frame dimensions with proper bezel proportions
        bezel = 24  # Thinner, more realistic bezel
        button_area = 12  # Extra space for side buttons
        frame_width = spec.screen_size[0] + (bezel * 2) + button_area
        frame_height = spec.screen_size[1] + (bezel * 2)

        # Create frame with transparency
        frame = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        # Base frame color (titanium gray)
        base_r, base_g, base_b = spec.frame_color[:3]

        # Draw outer frame (device body) - slightly offset for button area
        body_left = button_area
        draw.rounded_rectangle(
            [body_left, 0, frame_width - 1, frame_height - 1],
            radius=spec.corner_radius,
            fill=spec.frame_color
        )

        # Draw titanium edge highlight (top/left lighter)
        highlight_color = (min(255, base_r + 40), min(255, base_g + 40), min(255, base_b + 40), 255)
        draw.rounded_rectangle(
            [body_left + 2, 2, frame_width - 3, frame_height - 3],
            radius=spec.corner_radius - 2,
            outline=highlight_color,
            width=2
        )

        # Draw darker inner edge for depth
        inner_edge_color = (max(0, base_r - 30), max(0, base_g - 30), max(0, base_b - 30), 255)
        draw.rounded_rectangle(
            [body_left + bezel - 3, bezel - 3,
             body_left + bezel + spec.screen_size[0] + 2, bezel + spec.screen_size[1] + 2],
            radius=spec.corner_radius - 15,
            fill=inner_edge_color
        )

        # Draw screen bezel (very dark, almost black)
        screen_bezel_color = (10, 10, 12, 255)
        draw.rounded_rectangle(
            [body_left + bezel - 1, bezel - 1,
             body_left + bezel + spec.screen_size[0], bezel + spec.screen_size[1]],
            radius=spec.corner_radius - 16,
            fill=screen_bezel_color
        )

        # Draw screen area
        screen_left = body_left + bezel
        screen_top = bezel
        draw.rounded_rectangle(
            [screen_left, screen_top,
             screen_left + spec.screen_size[0] - 1, screen_top + spec.screen_size[1] - 1],
            radius=spec.corner_radius - 18,
            fill=(0, 0, 0, 255)
        )

        # Add Dynamic Island (proportional to screen size)
        island_width = int(spec.screen_size[0] * 0.19)  # ~19% of screen width
        island_height = int(island_width * 0.32)
        island_x = screen_left + (spec.screen_size[0] - island_width) // 2
        island_y = screen_top + int(spec.screen_size[1] * 0.012)
        draw.rounded_rectangle(
            [island_x, island_y, island_x + island_width, island_y + island_height],
            radius=island_height // 2,
            fill=(0, 0, 0, 255)
        )

        # Draw side buttons
        self._draw_side_buttons(draw, frame_height, spec)

        # Add edge reflections for realism
        self._add_edge_reflections(frame, body_left, frame_width, frame_height, spec)

        # Update screen offset for this frame layout
        spec.screen_offset = (screen_left, screen_top)

        return frame

    def _draw_side_buttons(self, draw: ImageDraw.Draw, frame_height: int, spec: DeviceSpec) -> None:
        """Draw realistic side buttons (volume, action button, power)."""
        base_r, base_g, base_b = spec.frame_color[:3]
        button_color = (max(0, base_r - 15), max(0, base_g - 15), max(0, base_b - 15), 255)
        button_highlight = (min(255, base_r + 20), min(255, base_g + 20), min(255, base_b + 20), 255)

        # Left side - Action Button (circle)
        action_y = int(frame_height * 0.15)
        action_size = 28
        draw.ellipse(
            [0, action_y, action_size, action_y + action_size],
            fill=button_color,
            outline=button_highlight
        )

        # Left side - Volume Up
        vol_up_y = int(frame_height * 0.22)
        vol_height = int(frame_height * 0.045)
        draw.rounded_rectangle(
            [0, vol_up_y, 8, vol_up_y + vol_height],
            radius=4,
            fill=button_color
        )

        # Left side - Volume Down
        vol_down_y = vol_up_y + vol_height + 15
        draw.rounded_rectangle(
            [0, vol_down_y, 8, vol_down_y + vol_height],
            radius=4,
            fill=button_color
        )

        # Right side - Power button (would need to extend frame, skip for now)

    def _add_edge_reflections(self, frame: Image.Image, body_left: int,
                               frame_width: int, frame_height: int, spec: DeviceSpec) -> None:
        """Add subtle edge reflections for metallic look."""
        # Create a gradient overlay for the top edge
        overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Top highlight gradient (subtle)
        for i in range(8):
            alpha = int(25 - i * 3)
            if alpha > 0:
                y = i
                color = (255, 255, 255, alpha)
                draw.line(
                    [(body_left + spec.corner_radius, y),
                     (frame_width - spec.corner_radius, y)],
                    fill=color,
                    width=1
                )

        # Composite overlay
        frame.alpha_composite(overlay)
    
    def _apply_corner_mask(self, image: Image.Image, radius: int) -> Image.Image:
        """Apply rounded corner mask to an image."""
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            [0, 0, image.size[0] - 1, image.size[1] - 1],
            radius=radius,
            fill=255
        )
        
        # Apply mask
        output = image.copy()
        output.putalpha(mask)
        return output
    
    def _add_shadow(self, image: Image.Image,
                   offset: Tuple[int, int],
                   blur_radius: int) -> Image.Image:
        """Add a simple floating drop shadow behind the device."""
        # Generous padding so shadow can taper naturally
        padding = blur_radius * 3
        new_width = image.size[0] + padding * 2
        new_height = image.size[1] + padding * 2

        # Create canvas
        result = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))

        # Create shadow from device alpha channel
        shadow_shape = Image.new('RGBA', image.size, (0, 0, 0, 40))
        if image.mode == 'RGBA':
            shadow_shape.putalpha(
                Image.eval(image.split()[3], lambda a: min(a, 40))
            )

        # Place shadow with offset
        result.paste(shadow_shape, (padding + offset[0], padding + offset[1]), shadow_shape)

        # Blur for soft falloff
        result = result.filter(ImageFilter.GaussianBlur(blur_radius))

        # Place device on top
        result.paste(image, (padding, padding), image)

        return result
