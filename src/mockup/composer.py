"""
Mockup composer - brings together device frames, screenshots, and backgrounds.
"""

from PIL import Image
from typing import Tuple, Optional, List, Dict
from pathlib import Path

from .device_frame import DeviceFrame
from .background import BackgroundGenerator
from ..analysis.color_extractor import ColorExtractor


# Platform-optimized presets
PLATFORM_PRESETS: Dict[str, Dict] = {
    "twitter": {
        "size": (1200, 1500),  # 4:5 aspect ratio - fills mobile feed
        "device_scale": 0.82,  # Larger phone for visibility
        "description": "Optimized for Twitter/X single image (4:5)"
    },
    "twitter4": {
        "size": (1200, 1200),  # 1:1 aspect ratio - for 4-image grid
        "device_scale": 0.72,  # Smaller to fit full phone in square
        "description": "Twitter/X 4-image grid (1:1, full phone visible)"
    },
    "instagram": {
        "size": (1080, 1350),  # 4:5 aspect ratio - Instagram optimal
        "device_scale": 0.82,
        "description": "Optimized for Instagram feed (4:5)"
    },
    "square": {
        "size": (1200, 1200),  # 1:1 - universal
        "device_scale": 0.75,
        "description": "Square format - works everywhere (1:1)"
    },
    "story": {
        "size": (1080, 1920),  # 9:16 - stories/reels
        "device_scale": 0.70,
        "description": "Stories/Reels format (9:16)"
    },
    "wide": {
        "size": (1600, 900),  # 16:9 - desktop/YouTube thumbnails
        "device_scale": 0.85,
        "description": "Wide format for desktop/thumbnails (16:9)"
    },
}


class MockupComposer:
    """
    Composes final mockup images from screenshots.
    Handles the full pipeline: color extraction -> background generation -> device framing -> composition.
    """

    def __init__(self,
                 device: str = "iphone_17_pro_max",
                 output_size: Tuple[int, int] = None,
                 platform: str = None,
                 assets_path: str = None):
        """
        Initialize the mockup composer.

        Args:
            device: Device frame to use
            output_size: Custom output size (width, height). Ignored if platform is set.
            platform: Platform preset ('twitter', 'instagram', 'square', 'story', 'wide'). Defaults to 'twitter'.
            assets_path: Path to device frame assets
        """
        # Default to twitter if no platform specified
        if platform is None:
            platform = "twitter"
        self.platform = platform
        self.preset = PLATFORM_PRESETS.get(platform)

        # Use preset size or custom size or default
        if self.preset:
            self.output_size = self.preset["size"]
            self.default_device_scale = self.preset["device_scale"]
        else:
            self.output_size = output_size or (2400, 2400)
            self.default_device_scale = 0.7

        self.device_frame = DeviceFrame(device=device, assets_path=assets_path)
        self.background_gen = BackgroundGenerator(*self.output_size)
    
    def create_mockup(self,
                     screenshot_path: str = None,
                     screenshot: Image.Image = None,
                     background_style: str = "flowing",
                     custom_colors: List[Tuple[int, int, int]] = None,
                     device_scale: float = None,
                     device_angle: float = 0,
                     device_position: Tuple[float, float] = (0.5, 0.5)) -> Image.Image:
        """
        Create a complete mockup from a screenshot.
        
        Args:
            screenshot_path: Path to screenshot file
            screenshot: PIL Image of screenshot (alternative to path)
            background_style: Style of background ('flowing', 'gradient', 'blobs', 'waves')
            custom_colors: Override extracted colors with custom palette
            device_scale: Scale of device relative to canvas (0.0 - 1.0)
            device_angle: Rotation angle in degrees
            device_position: Position of device center as fraction of canvas (0.0 - 1.0)
        
        Returns:
            Final composed mockup image
        """
        # Use preset device scale if not specified
        if device_scale is None:
            device_scale = self.default_device_scale

        # Load screenshot
        if screenshot_path:
            screenshot = Image.open(screenshot_path).convert('RGBA')
        elif screenshot is None:
            raise ValueError("Either screenshot_path or screenshot must be provided")
        
        # Extract colors from screenshot
        if custom_colors:
            colors = custom_colors
        else:
            extractor = ColorExtractor(image=screenshot)
            colors = extractor.get_complementary_colors()

        # Generate background (pass screenshot for 'expand' style)
        background = self.background_gen.generate(
            colors,
            style=background_style,
            source_image=screenshot if background_style == "expand" else None
        )
        background = background.convert('RGBA')
        
        # Create device mockup with screenshot
        device_mockup = self.device_frame.composite_screenshot(
            screenshot,
            add_shadow=True,
            shadow_offset=(40, 50),
            shadow_blur=80
        )
        
        # Scale device to fit
        device_height = int(self.output_size[1] * device_scale)
        aspect_ratio = device_mockup.size[0] / device_mockup.size[1]
        device_width = int(device_height * aspect_ratio)
        device_mockup = device_mockup.resize((device_width, device_height), Image.Resampling.LANCZOS)
        
        # Rotate if needed
        if device_angle != 0:
            device_mockup = device_mockup.rotate(
                device_angle, 
                expand=True, 
                resample=Image.Resampling.BICUBIC
            )
        
        # Calculate position
        pos_x = int((self.output_size[0] - device_mockup.size[0]) * device_position[0])
        pos_y = int((self.output_size[1] - device_mockup.size[1]) * device_position[1])
        
        # Composite device onto background
        background.paste(device_mockup, (pos_x, pos_y), device_mockup)
        
        return background
    
    def create_multi_device_mockup(self,
                                   screenshots: List[str],
                                   background_style: str = "flowing",
                                   layout: str = "stacked") -> Image.Image:
        """
        Create a mockup with multiple devices/screenshots.
        
        Args:
            screenshots: List of screenshot paths
            background_style: Background style
            layout: 'stacked', 'side-by-side', 'carousel'
        
        Returns:
            Composed multi-device mockup
        """
        if not screenshots:
            raise ValueError("At least one screenshot required")
        
        # Extract colors from first screenshot for consistent background
        extractor = ColorExtractor(image_path=screenshots[0])
        colors = extractor.get_complementary_colors()
        
        # Generate background
        background = self.background_gen.generate(colors, style=background_style)
        background = background.convert('RGBA')
        
        # Position devices based on layout
        positions = self._get_layout_positions(len(screenshots), layout)
        scales = self._get_layout_scales(len(screenshots), layout)
        angles = self._get_layout_angles(len(screenshots), layout)
        
        for i, screenshot_path in enumerate(screenshots):
            screenshot = Image.open(screenshot_path).convert('RGBA')
            
            # Create device mockup
            device_mockup = self.device_frame.composite_screenshot(
                screenshot,
                add_shadow=True,
                shadow_offset=(30, 40),
                shadow_blur=60
            )
            
            # Scale
            scale = scales[i]
            device_height = int(self.output_size[1] * scale)
            aspect_ratio = device_mockup.size[0] / device_mockup.size[1]
            device_width = int(device_height * aspect_ratio)
            device_mockup = device_mockup.resize((device_width, device_height), Image.Resampling.LANCZOS)
            
            # Rotate
            if angles[i] != 0:
                device_mockup = device_mockup.rotate(
                    angles[i],
                    expand=True,
                    resample=Image.Resampling.BICUBIC
                )
            
            # Position
            pos = positions[i]
            pos_x = int((self.output_size[0] - device_mockup.size[0]) * pos[0])
            pos_y = int((self.output_size[1] - device_mockup.size[1]) * pos[1])
            
            # Composite
            background.paste(device_mockup, (pos_x, pos_y), device_mockup)
        
        return background
    
    def _get_layout_positions(self, count: int, layout: str) -> List[Tuple[float, float]]:
        """Get device positions for a layout."""
        if layout == "stacked":
            if count == 1:
                return [(0.5, 0.5)]
            elif count == 2:
                return [(0.3, 0.6), (0.7, 0.4)]
            else:
                return [(0.2, 0.7), (0.5, 0.4), (0.8, 0.6)]
        elif layout == "side-by-side":
            if count == 1:
                return [(0.5, 0.5)]
            elif count == 2:
                return [(0.3, 0.5), (0.7, 0.5)]
            else:
                return [(0.2, 0.5), (0.5, 0.5), (0.8, 0.5)]
        elif layout == "carousel":
            if count == 1:
                return [(0.5, 0.5)]
            elif count == 2:
                return [(0.35, 0.5), (0.65, 0.5)]
            else:
                return [(0.15, 0.55), (0.5, 0.45), (0.85, 0.55)]
        return [(0.5, 0.5)] * count
    
    def _get_layout_scales(self, count: int, layout: str) -> List[float]:
        """Get device scales for a layout."""
        if count == 1:
            return [0.75]
        elif count == 2:
            if layout == "stacked":
                return [0.55, 0.55]
            return [0.5, 0.5]
        else:
            if layout == "carousel":
                return [0.4, 0.5, 0.4]
            return [0.4, 0.4, 0.4]
    
    def _get_layout_angles(self, count: int, layout: str) -> List[float]:
        """Get device rotation angles for a layout."""
        if layout == "stacked":
            if count == 2:
                return [-5, 5]
            elif count >= 3:
                return [-8, 0, 8]
        elif layout == "carousel":
            if count >= 3:
                return [-15, 0, 15]
        return [0] * count
    
    def save(self, image: Image.Image, output_path: str, 
             format: str = "PNG", quality: int = 95) -> str:
        """
        Save the mockup to a file.
        
        Args:
            image: The mockup image to save
            output_path: Path to save to
            format: Image format (PNG, JPEG, WEBP)
            quality: Quality for lossy formats
        
        Returns:
            Path to saved file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        if format.upper() == "JPEG":
            # Convert to RGB for JPEG
            image = image.convert('RGB')
        
        image.save(output, format=format, quality=quality)
        return str(output)
