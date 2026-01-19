"""
Video mockup generator - creates phone mockup videos from screen recordings.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image

from .device_frame import DeviceFrame
from .background import BackgroundGenerator
from .composer import PLATFORM_PRESETS
from ..analysis.color_extractor import ColorExtractor, resolve_colors


class VideoMockupGenerator:
    """Generate video mockups with phone frames and backgrounds."""

    def __init__(self,
                 device: str = "iphone_17_pro_max",
                 platform: str = "twitter"):
        self.device = device
        self.platform = platform
        self.preset = PLATFORM_PRESETS.get(platform, PLATFORM_PRESETS["twitter"])
        self.output_size = self.preset["size"]
        self.device_scale = self.preset["device_scale"]

        self.device_frame = DeviceFrame(device=device)
        self.background_gen = BackgroundGenerator(*self.output_size)

        # Check ffmpeg is available
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg is required for video mockups. Install with: brew install ffmpeg")

    def create_video_mockup(self,
                           input_video: str,
                           output_path: str = None,
                           background_style: str = "expand",
                           colors: list = None) -> str:
        """
        Create a video mockup from a screen recording.

        Args:
            input_video: Path to input video file
            output_path: Output video path (optional)
            background_style: Background style to use
            colors: Custom colors (optional)

        Returns:
            Path to output video
        """
        input_path = Path(input_video)
        if not input_path.exists():
            raise FileNotFoundError(f"Video not found: {input_video}")

        if not output_path:
            output_path = input_path.parent / f"{input_path.stem}_mockup.mp4"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract first frame for color extraction and expand background
            first_frame_path = temp_path / "first_frame.png"
            self._extract_frame(input_video, str(first_frame_path), time=0)

            # Get video dimensions
            video_width, video_height = self._get_video_dimensions(input_video)

            # Resolve colors from first frame
            if not colors:
                colors = resolve_colors(screenshot_path=str(first_frame_path))

            # Generate background
            first_frame = Image.open(first_frame_path)
            if background_style == "expand":
                background = self.background_gen.generate(
                    colors, style="expand", source_image=first_frame
                )
            else:
                background = self.background_gen.generate(colors, style=background_style)

            background_path = temp_path / "background.png"
            background.save(background_path)

            # Generate phone frame overlay (with transparent screen)
            frame_overlay, screen_position, screen_size = self._create_frame_overlay(
                video_width, video_height
            )
            frame_overlay_path = temp_path / "frame_overlay.png"
            frame_overlay.save(frame_overlay_path)

            # Use ffmpeg to composite everything
            self._composite_video(
                input_video=input_video,
                background_path=str(background_path),
                frame_overlay_path=str(frame_overlay_path),
                output_path=str(output_path),
                screen_position=screen_position,
                screen_size=screen_size
            )

        return str(output_path)

    def _extract_frame(self, video_path: str, output_path: str, time: float = 0):
        """Extract a single frame from video."""
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(time),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    def _get_video_dimensions(self, video_path: str) -> Tuple[int, int]:
        """Get video width and height."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        width, height = result.stdout.strip().split(",")
        return int(width), int(height)

    def _create_frame_overlay(self,
                              video_width: int,
                              video_height: int) -> Tuple[Image.Image, Tuple[int, int], Tuple[int, int]]:
        """
        Create the phone frame overlay positioned for the output canvas.

        Returns:
            (frame_overlay_image, screen_position, screen_size)
        """
        # Get device spec for screen dimensions
        spec = self.device_frame.device_spec

        # Create frame without screenshot (transparent screen area)
        frame = self.device_frame._generate_frame()

        # Calculate scaled size for output
        device_height = int(self.output_size[1] * self.device_scale)
        aspect_ratio = frame.size[0] / frame.size[1]
        device_width = int(device_height * aspect_ratio)

        # Scale the frame
        frame_scaled = frame.resize((device_width, device_height), Image.Resampling.LANCZOS)

        # Calculate position (centered)
        pos_x = (self.output_size[0] - device_width) // 2
        pos_y = (self.output_size[1] - device_height) // 2

        # Create full canvas with transparent frame overlay
        overlay = Image.new('RGBA', self.output_size, (0, 0, 0, 0))
        overlay.paste(frame_scaled, (pos_x, pos_y), frame_scaled)

        # Calculate where the screen area is in the final output
        scale_factor = device_height / frame.size[1]
        screen_x = pos_x + int(spec.screen_offset[0] * scale_factor)
        screen_y = pos_y + int(spec.screen_offset[1] * scale_factor)
        screen_w = int(spec.screen_size[0] * scale_factor)
        screen_h = int(spec.screen_size[1] * scale_factor)

        return overlay, (screen_x, screen_y), (screen_w, screen_h)

    def _composite_video(self,
                        input_video: str,
                        background_path: str,
                        frame_overlay_path: str,
                        output_path: str,
                        screen_position: Tuple[int, int],
                        screen_size: Tuple[int, int]):
        """Use ffmpeg to composite background + video + frame overlay."""
        screen_x, screen_y = screen_position
        screen_w, screen_h = screen_size

        # Complex filter to:
        # 1. Scale input video to fit screen area
        # 2. Overlay scaled video onto background at screen position
        # 3. Overlay phone frame on top
        filter_complex = (
            f"[1:v]scale={screen_w}:{screen_h}:force_original_aspect_ratio=decrease,"
            f"pad={screen_w}:{screen_h}:(ow-iw)/2:(oh-ih)/2:color=black@0[scaled];"
            f"[0:v][scaled]overlay={screen_x}:{screen_y}[with_video];"
            f"[with_video][2:v]overlay=0:0[out]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", background_path,      # Input 0: background
            "-i", input_video,                         # Input 1: video
            "-loop", "1", "-i", frame_overlay_path,   # Input 2: frame overlay
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-map", "1:a?",  # Keep audio if present
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-shortest",
            "-pix_fmt", "yuv420p",
            output_path
        ]

        subprocess.run(cmd, check=True)


def quick_video_mockup(input_video: str,
                       output_path: str = None,
                       background_style: str = "expand",
                       platform: str = "twitter",
                       colors: list = None) -> str:
    """
    Quick function to create a video mockup.

    Args:
        input_video: Path to screen recording
        output_path: Output video path
        background_style: Background style
        platform: Platform preset
        colors: Custom colors

    Returns:
        Path to output video
    """
    generator = VideoMockupGenerator(platform=platform)
    return generator.create_video_mockup(
        input_video=input_video,
        output_path=output_path,
        background_style=background_style,
        colors=colors
    )
