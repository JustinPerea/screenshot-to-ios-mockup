# Screenshot to Social Mockup Generator

Turn app screenshots into professional social media mockups with realistic iPhone frames and beautiful backgrounds.

## Claude Code Setup

Copy and paste this into Claude Code:

```
Clone https://github.com/JustinPerea/screenshot-to-ios-mockup.git and set it up for me.

1. Install dependencies: pip install -r requirements.txt
2. Verify the imports work by testing the modules

This tool creates professional iPhone mockups from screenshots for social media. Here's what I need to know:

COMMANDS:
- python main.py screenshot <image> - Create a single mockup
- python main.py batch <folder> - Process all screenshots in a folder
- python main.py styles - List background styles
- python main.py platforms - List platform presets

BACKGROUND STYLES (-s flag):
- expand: Blurred screenshot fill (default)
- aurora: Northern lights effect
- mesh: Smooth gradient
- glass: Frosted glass
- sunset/ocean: Color gradients

PLATFORM PRESETS (-p flag):
- twitter: 1200x1500, 4:5 ratio (default)
- instagram: 1080x1350, 4:5 ratio
- story: 1080x1920, 9:16 ratio
- square: 1200x1200, 1:1 ratio

OUTPUT: Mockups save to ./output/ folder by default

After setup, show me how to create my first mockup.
```

---

## Background Styles

### Expand (Default)
Blurs and expands your screenshot to fill the background, creating the popular "TV news phone video" effect. The colors automatically match your content.

<img src="examples/output/orbit-expand.png" width="400">

```bash
python main.py screenshot image.png -s expand
```

---

### Aurora
Creates smooth vertical color bands inspired by the northern lights. Uses soft gaussian gradients for an elegant, ethereal look.

<img src="examples/output/orbit-aurora.png" width="400">

```bash
python main.py screenshot image.png -s aurora
```

---

### Mesh
Generates a smooth multi-point gradient by blending colors from corners and center. Clean, professional, and modern.

<img src="examples/output/orbit-mesh.png" width="400">

```bash
python main.py screenshot image.png -s mesh
```

---

### Glass
Frosted glass effect with subtle noise texture and soft color overlays. Modern and minimal.

<img src="examples/output/orbit-glass.png" width="400">

```bash
python main.py screenshot image.png -s glass
```

---

### Sunset
Warm vertical gradient transitioning from orange to pink to purple. Great for lifestyle and creative apps.

<img src="examples/output/orbit-sunset.png" width="400">

```bash
python main.py screenshot image.png -s sunset
```

---

### Ocean
Cool gradient with blues and teals flowing diagonally. Perfect for productivity and utility apps.

<img src="examples/output/orbit-ocean.png" width="400">

```bash
python main.py screenshot image.png -s ocean
```

---

## Features

- **Realistic iPhone 17 Pro Max frame** - Procedurally generated with Dynamic Island, side buttons, and titanium finish
- **Multiple background styles** - `expand`, `mesh`, `aurora`, `glass`, `sunset`, `ocean`, and more
- **Platform presets** - Optimized sizes for Twitter, Instagram, Stories, etc.
- **Color extraction** - Auto-extracts colors from screenshots or use preset palettes
- **Video support** - Create video mockups from screen recordings (requires ffmpeg)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate a mockup from a screenshot
python main.py screenshot path/to/screenshot.png

# Process a folder of screenshots
python main.py batch path/to/folder/
```

## Background Styles

| Style | Description |
|-------|-------------|
| `expand` | Blurred screenshot fill (like TV news) - **default** |
| `mesh` | Smooth multi-point gradient |
| `aurora` | Northern lights vertical bands |
| `glass` | Frosted glass effect |
| `sunset` | Warm orange to purple gradient |
| `ocean` | Cool blue to teal gradient |
| `soft` | Minimal pastel background |

```bash
python main.py screenshot image.png -s mesh
python main.py screenshot image.png -s aurora
```

## Platform Presets

| Platform | Size | Use Case |
|----------|------|----------|
| `twitter` | 1200x1500 (4:5) | Twitter/X feed - **default** |
| `instagram` | 1080x1350 (4:5) | Instagram feed |
| `story` | 1080x1920 (9:16) | Stories/Reels |
| `square` | 1200x1200 (1:1) | Universal |
| `wide` | 1600x900 (16:9) | Desktop/thumbnails |

```bash
python main.py screenshot image.png -p instagram
python main.py screenshot image.png -p story
```

## Color Options

```bash
# Auto-extract from screenshot (default)
python main.py screenshot image.png

# Use a preset palette
python main.py screenshot image.png -c sunset
python main.py screenshot image.png -c ocean

# Use custom hex colors
python main.py screenshot image.png -c "#FF5733,#3498DB,#2ECC71"
```

Available palettes: `vibrant`, `pastel`, `dark`, `warm`, `cool`, `sunset`, `ocean`, `forest`, `berry`, `monochrome`

## Video Mockups

Create video mockups from screen recordings (requires ffmpeg):

```bash
# Install ffmpeg (macOS)
brew install ffmpeg

# Generate video mockup
python main.py video recording.mov
python main.py video recording.mp4 -s mesh -p story
```

## All Commands

```bash
python main.py screenshot <image>  # Single screenshot mockup
python main.py batch <folder>      # Batch process folder
python main.py video <video>       # Video mockup
python main.py styles              # List background styles
python main.py colors              # List color palettes
python main.py platforms           # List platform presets
```

## Examples

```bash
# Twitter post with blurred background
python main.py screenshot app.png -s expand -p twitter

# Instagram story with aurora style
python main.py screenshot app.png -s aurora -p story

# Batch process with sunset colors
python main.py batch screenshots/ -s mesh -c sunset
```

## More Examples

<table>
  <tr>
    <td align="center"><strong>Apple Music</strong><br><img src="examples/output/apple-music-expand.png" width="400"></td>
    <td align="center"><strong>KakaoBank</strong><br><img src="examples/output/kakaobank-expand.png" width="400"></td>
  </tr>
  <tr>
    <td align="center"><strong>Open</strong><br><img src="examples/output/open-expand.png" width="400"></td>
    <td align="center"><strong>Sunlitt</strong><br><img src="examples/output/sunlitt-expand.png" width="400"></td>
  </tr>
  <tr>
    <td align="center"><strong>Apple Music (Aurora)</strong><br><img src="examples/output/apple-music-aurora.png" width="400"></td>
    <td align="center"><strong>KakaoBank (Mesh)</strong><br><img src="examples/output/kakaobank-mesh.png" width="400"></td>
  </tr>
  <tr>
    <td align="center"><strong>Open (Glass)</strong><br><img src="examples/output/open-glass.png" width="400"></td>
    <td align="center"><strong>Sunlitt (Sunset)</strong><br><img src="examples/output/sunlitt-sunset.png" width="400"></td>
  </tr>
  <tr>
    <td align="center"><strong>Apple Music (Ocean)</strong><br><img src="examples/output/apple-music-ocean.png" width="400"></td>
    <td align="center"><strong>KakaoBank (Aurora)</strong><br><img src="examples/output/kakaobank-aurora.png" width="400"></td>
  </tr>
  <tr>
    <td align="center"><strong>Open (Sunset)</strong><br><img src="examples/output/open-sunset.png" width="400"></td>
    <td align="center"><strong>Sunlitt (Ocean)</strong><br><img src="examples/output/sunlitt-ocean.png" width="400"></td>
  </tr>
</table>

---

Built for the "build in public" community.
