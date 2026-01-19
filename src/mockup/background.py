"""
Abstract background generator for mockups.
Creates flowing gradients and organic shapes that complement the app colors.
"""

from PIL import Image, ImageDraw, ImageFilter
from typing import List, Tuple, Optional
import math
import random


class BackgroundGenerator:
    """Generate beautiful abstract backgrounds for device mockups."""
    
    def __init__(self, width: int = 2400, height: int = 2400):
        self.width = width
        self.height = height
    
    def generate(self,
                colors: List[Tuple[int, int, int]],
                style: str = "mesh",
                source_image: Image.Image = None) -> Image.Image:
        """
        Generate a background with the given color palette.

        Args:
            colors: List of RGB colors to use
            style: Background style - 'mesh', 'gradient', 'aurora', 'soft', 'flowing', 'waves', 'expand'
            source_image: Optional source image for 'expand' style

        Returns:
            Generated background image
        """
        if style == "expand" and source_image:
            return self._generate_expand(source_image, colors)
        elif style == "mesh":
            return self._generate_mesh(colors)
        elif style == "gradient":
            return self._generate_gradient(colors)
        elif style == "aurora":
            return self._generate_aurora(colors)
        elif style == "soft":
            return self._generate_soft(colors)
        elif style == "glass":
            return self._generate_glass(colors)
        elif style == "sunset":
            return self._generate_sunset(colors)
        elif style == "ocean":
            return self._generate_ocean(colors)
        elif style == "flowing":
            return self._generate_flowing(colors)
        elif style == "waves":
            return self._generate_waves(colors)
        else:
            return self._generate_mesh(colors)
    
    def _generate_flowing(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate flowing organic shapes like in professional mockups."""
        # Start with a gradient base
        img = self._generate_gradient(colors[:2] if len(colors) >= 2 else colors + colors)
        
        # Add flowing organic shapes
        for i, color in enumerate(colors[:4]):
            # Create multiple layers of flowing shapes
            shape_layer = self._create_flowing_shape(
                color=(*color, 60 + i * 20),  # Varying opacity
                seed=i * 42,
                scale=0.8 - (i * 0.15)
            )
            img = Image.alpha_composite(img.convert('RGBA'), shape_layer)
        
        # Apply subtle blur for softness
        img = img.filter(ImageFilter.GaussianBlur(radius=3))
        
        return img
    
    def _create_flowing_shape(self, 
                             color: Tuple[int, int, int, int],
                             seed: int = 0,
                             scale: float = 1.0) -> Image.Image:
        """Create a single flowing organic shape."""
        random.seed(seed)
        
        layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        
        # Generate bezier-like flowing path
        center_x = self.width * (0.3 + random.random() * 0.4)
        center_y = self.height * (0.3 + random.random() * 0.4)
        
        # Create organic blob using multiple overlapping ellipses
        num_ellipses = random.randint(8, 15)
        
        for _ in range(num_ellipses):
            # Random position around center
            offset_x = (random.random() - 0.5) * self.width * 0.5 * scale
            offset_y = (random.random() - 0.5) * self.height * 0.5 * scale
            
            x = center_x + offset_x
            y = center_y + offset_y
            
            # Random ellipse dimensions
            w = random.randint(int(200 * scale), int(600 * scale))
            h = random.randint(int(300 * scale), int(800 * scale))
            
            # Draw ellipse
            draw.ellipse(
                [x - w, y - h, x + w, y + h],
                fill=color
            )
        
        # Heavy blur to blend shapes together
        layer = layer.filter(ImageFilter.GaussianBlur(radius=80))
        
        return layer
    
    def _generate_gradient(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate a smooth gradient background."""
        img = Image.new('RGB', (self.width, self.height))
        
        if len(colors) < 2:
            colors = colors + [(255, 255, 255)]
        
        c1, c2 = colors[0], colors[1]
        
        # Create diagonal gradient
        for y in range(self.height):
            for x in range(self.width):
                # Diagonal interpolation factor
                factor = (x / self.width + y / self.height) / 2
                
                r = int(c1[0] + (c2[0] - c1[0]) * factor)
                g = int(c1[1] + (c2[1] - c1[1]) * factor)
                b = int(c1[2] + (c2[2] - c1[2]) * factor)
                
                img.putpixel((x, y), (r, g, b))
        
        return img
    
    def _generate_blobs(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate soft blob shapes."""
        # Start with lightest color as base
        base_color = self._lighten_color(colors[0], 0.8) if colors else (240, 240, 240)
        img = Image.new('RGBA', (self.width, self.height), (*base_color, 255))
        
        # Add multiple blob layers
        for i, color in enumerate(colors[:5]):
            blob = self._create_blob(
                color=(*color, 40 + i * 15),
                x=random.randint(0, self.width),
                y=random.randint(0, self.height),
                size=random.randint(400, 1000)
            )
            img = Image.alpha_composite(img, blob)
        
        return img
    
    def _create_blob(self, 
                    color: Tuple[int, int, int, int],
                    x: int, y: int, 
                    size: int) -> Image.Image:
        """Create a single soft blob."""
        layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        
        draw.ellipse(
            [x - size, y - size, x + size, y + size],
            fill=color
        )
        
        # Blur to soften
        layer = layer.filter(ImageFilter.GaussianBlur(radius=size // 3))
        
        return layer
    
    def _generate_waves(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate wave-like flowing patterns."""
        img = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 255))
        
        for i, color in enumerate(colors[:3]):
            wave_layer = self._create_wave_layer(
                color=(*color, 80),
                frequency=0.005 + i * 0.002,
                amplitude=200 + i * 50,
                phase=i * math.pi / 3
            )
            img = Image.alpha_composite(img, wave_layer)
        
        img = img.filter(ImageFilter.GaussianBlur(radius=5))
        return img
    
    def _create_wave_layer(self,
                          color: Tuple[int, int, int, int],
                          frequency: float,
                          amplitude: float,
                          phase: float) -> Image.Image:
        """Create a single wave layer."""
        layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        
        # Create wave polygon
        points = []
        
        # Top edge follows wave
        for x in range(0, self.width + 10, 10):
            y = self.height // 2 + int(math.sin(x * frequency + phase) * amplitude)
            points.append((x, y))
        
        # Complete polygon by going to bottom
        points.append((self.width, self.height))
        points.append((0, self.height))
        
        draw.polygon(points, fill=color)
        
        # Blur for softness
        layer = layer.filter(ImageFilter.GaussianBlur(radius=30))
        
        return layer
    
    def _lighten_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Lighten a color by mixing with white."""
        return (
            int(color[0] + (255 - color[0]) * factor),
            int(color[1] + (255 - color[1]) * factor),
            int(color[2] + (255 - color[2]) * factor)
        )

    def _generate_expand(self, source: Image.Image, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """
        Generate background by expanding and blurring the source screenshot.
        Creates the 'TV news phone video' effect where background matches content.
        """
        # Convert to RGB if needed
        if source.mode != 'RGB':
            source = source.convert('RGB')

        src_w, src_h = source.size
        src_aspect = src_w / src_h
        target_aspect = self.width / self.height

        # Scale to cover the entire canvas (crop to fill)
        if src_aspect > target_aspect:
            # Source is wider - scale by height
            new_height = self.height
            new_width = int(new_height * src_aspect)
        else:
            # Source is taller - scale by width
            new_width = self.width
            new_height = int(new_width / src_aspect)

        # Scale up significantly to push UI elements off canvas
        scale_factor = 1.8
        new_width = int(new_width * scale_factor)
        new_height = int(new_height * scale_factor)

        # Resize the source image
        expanded = source.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center crop to canvas size
        left = (new_width - self.width) // 2
        top = (new_height - self.height) // 2
        expanded = expanded.crop((left, top, left + self.width, top + self.height))

        # Apply very heavy blur to remove all detail
        blur_radius = min(self.width, self.height) // 8  # ~150px for 1200px canvas
        expanded = expanded.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        expanded = expanded.filter(ImageFilter.GaussianBlur(radius=blur_radius // 2))  # Second pass

        # Optional: Add subtle darkening overlay so the sharp device pops
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 40))
        expanded = Image.alpha_composite(expanded.convert('RGBA'), overlay)

        # Optional: Add subtle color tint from extracted colors for cohesion
        if colors:
            tint_color = colors[0]
            tint = Image.new('RGBA', (self.width, self.height), (*tint_color, 20))
            expanded = Image.alpha_composite(expanded, tint)

        return expanded.convert('RGB')

    def _generate_mesh(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate a smooth mesh gradient - clean, professional look."""
        # Ensure we have enough colors
        while len(colors) < 4:
            colors = colors + [self._lighten_color(colors[0], 0.3)]

        img = Image.new('RGB', (self.width, self.height))

        # Create smooth multi-point gradient using distance-based blending
        # Place color points at corners and edges
        points = [
            (0, 0, colors[0]),
            (self.width, 0, colors[1] if len(colors) > 1 else colors[0]),
            (0, self.height, colors[2] if len(colors) > 2 else colors[0]),
            (self.width, self.height, colors[3] if len(colors) > 3 else colors[1]),
            (self.width // 2, self.height // 2, self._lighten_color(colors[0], 0.4)),
        ]

        for y in range(self.height):
            for x in range(self.width):
                # Calculate weighted average based on distance to each point
                total_weight = 0
                r, g, b = 0.0, 0.0, 0.0

                for px, py, color in points:
                    # Use inverse distance weighting with power for smoothness
                    dist = math.sqrt((x - px) ** 2 + (y - py) ** 2) + 1
                    weight = 1 / (dist ** 1.5)
                    total_weight += weight
                    r += color[0] * weight
                    g += color[1] * weight
                    b += color[2] * weight

                img.putpixel((x, y), (
                    int(r / total_weight),
                    int(g / total_weight),
                    int(b / total_weight)
                ))

        # Subtle blur for extra smoothness
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        return img

    def _generate_aurora(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate aurora/northern lights style - smooth vertical bands."""
        # Light base color
        base = self._lighten_color(colors[0], 0.85) if colors else (245, 245, 250)
        img = Image.new('RGB', (self.width, self.height), base)

        # Create smooth vertical color bands
        num_bands = 3
        band_width = self.width // num_bands

        for i, color in enumerate(colors[:num_bands]):
            band_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(band_img)

            # Position band with some randomness
            center_x = int(band_width * (i + 0.5) + (random.random() - 0.5) * band_width * 0.3)

            # Draw vertical gradient band
            for x in range(self.width):
                # Gaussian falloff from center
                dist = abs(x - center_x)
                alpha = int(60 * math.exp(-(dist ** 2) / (2 * (band_width * 0.4) ** 2)))

                if alpha > 0:
                    draw.line([(x, 0), (x, self.height)], fill=(*color, alpha))

            # Heavy vertical blur
            band_img = band_img.filter(ImageFilter.GaussianBlur(radius=50))
            img = Image.alpha_composite(img.convert('RGBA'), band_img)

        return img.convert('RGB')

    def _generate_soft(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate a soft, subtle background - minimal and clean."""
        # Very light pastel base
        if colors:
            base = self._lighten_color(colors[0], 0.9)
        else:
            base = (248, 248, 250)

        img = Image.new('RGB', (self.width, self.height), base)

        # Add very subtle gradient overlay
        if len(colors) >= 2:
            accent = self._lighten_color(colors[1], 0.7)

            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Subtle corner accent
            for i in range(self.width // 2):
                alpha = int(25 * (1 - i / (self.width // 2)))
                if alpha > 0:
                    # Bottom right corner glow
                    draw.ellipse([
                        self.width - i * 3,
                        self.height - i * 3,
                        self.width + i,
                        self.height + i
                    ], fill=(*accent, alpha))

            overlay = overlay.filter(ImageFilter.GaussianBlur(radius=100))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        return img

    def _generate_glass(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate frosted glass effect - modern and elegant."""
        # Create base with primary color, very light
        base = self._lighten_color(colors[0], 0.7) if colors else (230, 235, 240)
        img = Image.new('RGB', (self.width, self.height), base)

        # Add noise texture for frosted effect
        noise = Image.new('RGB', (self.width, self.height))
        for y in range(self.height):
            for x in range(self.width):
                variation = random.randint(-8, 8)
                noise.putpixel((x, y), (
                    max(0, min(255, base[0] + variation)),
                    max(0, min(255, base[1] + variation)),
                    max(0, min(255, base[2] + variation))
                ))

        noise = noise.filter(ImageFilter.GaussianBlur(radius=3))

        if len(colors) >= 2:
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            for i, color in enumerate(colors[:3]):
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)
                size = random.randint(600, 1200)
                draw.ellipse([x - size, y - size, x + size, y + size],
                            fill=(*color, 20))

            overlay = overlay.filter(ImageFilter.GaussianBlur(radius=200))
            noise = Image.alpha_composite(noise.convert('RGBA'), overlay).convert('RGB')

        return noise

    def _generate_sunset(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate warm sunset gradient - orange, pink, purple tones."""
        sunset_colors = [
            (255, 150, 100),  # Warm orange
            (255, 120, 150),  # Pink
            (180, 100, 200),  # Purple
            (100, 80, 160),   # Deep purple
        ]

        if colors:
            sunset_colors[0] = self._blend_colors(sunset_colors[0], colors[0], 0.3)

        img = Image.new('RGB', (self.width, self.height))

        for y in range(self.height):
            factor = y / self.height
            if factor < 0.33:
                t = factor / 0.33
                color = self._blend_colors(sunset_colors[0], sunset_colors[1], t)
            elif factor < 0.66:
                t = (factor - 0.33) / 0.33
                color = self._blend_colors(sunset_colors[1], sunset_colors[2], t)
            else:
                t = (factor - 0.66) / 0.34
                color = self._blend_colors(sunset_colors[2], sunset_colors[3], t)

            for x in range(self.width):
                img.putpixel((x, y), color)

        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        return img

    def _generate_ocean(self, colors: List[Tuple[int, int, int]]) -> Image.Image:
        """Generate cool ocean gradient - blues and teals."""
        ocean_colors = [
            (200, 230, 245),  # Light sky blue
            (100, 180, 220),  # Ocean blue
            (60, 140, 180),   # Deep teal
            (40, 100, 140),   # Deep ocean
        ]

        if colors:
            ocean_colors[1] = self._blend_colors(ocean_colors[1], colors[0], 0.3)

        img = Image.new('RGB', (self.width, self.height))

        for y in range(self.height):
            for x in range(self.width):
                factor = (x / self.width * 0.3 + y / self.height * 0.7)

                if factor < 0.33:
                    t = factor / 0.33
                    color = self._blend_colors(ocean_colors[0], ocean_colors[1], t)
                elif factor < 0.66:
                    t = (factor - 0.33) / 0.33
                    color = self._blend_colors(ocean_colors[1], ocean_colors[2], t)
                else:
                    t = (factor - 0.66) / 0.34
                    color = self._blend_colors(ocean_colors[2], ocean_colors[3], t)

                img.putpixel((x, y), color)

        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        return img

    def _blend_colors(self, c1: Tuple[int, int, int], c2: Tuple[int, int, int],
                      factor: float) -> Tuple[int, int, int]:
        """Blend two colors together."""
        return (
            int(c1[0] + (c2[0] - c1[0]) * factor),
            int(c1[1] + (c2[1] - c1[1]) * factor),
            int(c1[2] + (c2[2] - c1[2]) * factor)
        )
