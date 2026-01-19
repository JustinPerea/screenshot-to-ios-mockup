#!/usr/bin/env python3
"""
GitHub to Social - Generate beautiful social media mockups from your projects.

Usage:
    # Generate mockup from a screenshot
    python main.py screenshot path/to/screenshot.png
    
    # Analyze and generate from a local project
    python main.py project path/to/ios/project
    
    # Quick mockup with custom style
    python main.py screenshot image.png --style waves --output my_mockup.png
"""

import argparse
import sys
from pathlib import Path

from src.pipeline import GitHubToSocialPipeline, GitHubMockupPipeline, quick_mockup
from src.mockup.composer import MockupComposer, PLATFORM_PRESETS
from src.mockup.video_mockup import quick_video_mockup
from src.analysis.project_analyzer import ProjectAnalyzer
from src.analysis.color_extractor import (
    resolve_colors, get_available_palettes, PRESET_PALETTES
)


def cmd_screenshot(args):
    """Generate mockup from a single screenshot."""
    if not Path(args.screenshot).exists():
        print(f"Error: Screenshot not found: {args.screenshot}")
        return 1

    # Resolve colors from argument or screenshot
    colors = None
    if args.colors:
        colors = resolve_colors(color_arg=args.colors)
        print(f"Using colors: {args.colors}")
    else:
        colors = resolve_colors(screenshot_path=args.screenshot)
        print(f"Extracting colors from screenshot")

    print(f"Generating mockup from: {args.screenshot}")
    print(f"Style: {args.style}")
    if args.platform:
        preset = PLATFORM_PRESETS.get(args.platform, {})
        print(f"Platform: {args.platform} ({preset.get('size', 'custom')})")

    output_path = quick_mockup(
        screenshot_path=args.screenshot,
        output_path=args.output,
        background_style=args.style,
        device=args.device,
        colors=colors,
        platform=args.platform
    )

    print(f"Mockup saved to: {output_path}")
    return 0


def cmd_project(args):
    """Generate mockups from a project directory."""
    if not Path(args.project).exists():
        print(f"Error: Project not found: {args.project}")
        return 1
    
    pipeline = GitHubToSocialPipeline(
        project_path=args.project,
        output_dir=args.output or "./output",
        device=args.device
    )
    
    outputs = pipeline.run(
        background_style=args.style,
        capture_screenshots=args.capture,
        screenshot_count=args.count
    )
    
    if outputs:
        print("\nGenerated mockups:")
        for output in outputs:
            print(f"  - {output.mockup_path}")
    
    return 0


def cmd_analyze(args):
    """Analyze a project and show information."""
    if not Path(args.project).exists():
        print(f"Error: Project not found: {args.project}")
        return 1
    
    analyzer = ProjectAnalyzer(project_path=args.project)
    info = analyzer.analyze()
    
    print(f"\nProject Analysis: {info.name}")
    print(f"{'=' * 40}")
    print(f"Type:        {info.type}")
    print(f"Language:    {info.language}")
    print(f"Description: {info.description or 'N/A'}")
    print(f"Screenshots: {'Yes' if info.has_existing_screenshots else 'No'}")
    
    if info.colors:
        print(f"Colors:      {len(info.colors)} found")
        for i, color in enumerate(info.colors):
            print(f"  {i + 1}. RGB{color}")
    
    if info.key_features:
        print(f"\nKey Features:")
        for feature in info.key_features:
            print(f"  - {feature}")
    
    suggestions = analyzer.get_screenshot_suggestions()
    print(f"\nScreenshot Suggestions:")
    for suggestion in suggestions:
        print(f"  - {suggestion}")
    
    return 0


def cmd_styles(args):
    """Show available background styles with examples."""
    print("\nAvailable Background Styles:")
    print("=" * 40)
    print("  expand   - Blurred screenshot fill (like TV news)")
    print("  mesh     - Smooth mesh gradient (recommended)")
    print("  soft     - Minimal, subtle pastel background")
    print("  aurora   - Northern lights style vertical bands")
    print("  glass    - Frosted glass effect")
    print("  sunset   - Warm orange to purple gradient")
    print("  ocean    - Cool blue to teal gradient")
    print("  gradient - Simple diagonal gradient")
    print("  flowing  - Organic flowing shapes (legacy)")
    print("  waves    - Wave-like patterns")
    return 0


def cmd_colors(args):
    """Show available color palettes."""
    print("\nAvailable Color Palettes:")
    print("=" * 40)
    for name, colors in PRESET_PALETTES.items():
        # Convert RGB to hex for display
        hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors[:3]]
        print(f"  {name:12} - {', '.join(hex_colors)}...")
    print()
    print("Usage:")
    print("  --colors sunset          Use preset palette")
    print("  --colors \"#FF5733,#3498DB\"  Use custom hex colors")
    print("  (no flag)                Auto-extract from screenshot")
    return 0


def cmd_platforms(args):
    """Show available platform presets."""
    print("\nAvailable Platform Presets:")
    print("=" * 50)
    for name, preset in PLATFORM_PRESETS.items():
        size = preset["size"]
        scale = preset["device_scale"]
        desc = preset["description"]
        print(f"  {name:10} - {size[0]}x{size[1]} (scale: {scale}) - {desc}")
    print()
    print("Usage:")
    print("  --platform twitter       Optimize for Twitter/X feed")
    print("  --platform instagram     Optimize for Instagram feed")
    print("  --platform story         Optimize for Stories/Reels")
    print("  (no flag)                Default twitter preset")
    return 0


def cmd_video(args):
    """Generate video mockup from a screen recording."""
    if not Path(args.video).exists():
        print(f"Error: Video not found: {args.video}")
        return 1

    # Resolve colors if specified
    colors = None
    if args.colors:
        colors = resolve_colors(color_arg=args.colors)
        print(f"Using colors: {args.colors}")

    print(f"Generating video mockup from: {args.video}")
    print(f"Style: {args.style}")
    print(f"Platform: {args.platform}")
    print()

    try:
        output_path = quick_video_mockup(
            input_video=args.video,
            output_path=args.output,
            background_style=args.style,
            platform=args.platform,
            colors=colors
        )
        print(f"Video mockup saved to: {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_batch(args):
    """Generate mockups from all screenshots in a folder."""
    folder = Path(args.folder)
    if not folder.exists():
        print(f"Error: Folder not found: {args.folder}")
        return 1

    # Find all images
    screenshots = []
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']:
        screenshots.extend(folder.glob(ext))

    if not screenshots:
        print(f"No screenshots found in {args.folder}")
        return 1

    print(f"Found {len(screenshots)} screenshots in {args.folder}")
    print(f"Style: {args.style}")
    if args.colors:
        print(f"Colors: {args.colors}")
    if args.platform:
        preset = PLATFORM_PRESETS.get(args.platform, {})
        print(f"Platform: {args.platform} ({preset.get('size', 'custom')})")
    print()

    output_dir = Path(args.output) if args.output else folder / "mockups"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Pre-resolve colors if specified (use same palette for all)
    base_colors = None
    if args.colors:
        base_colors = resolve_colors(color_arg=args.colors)

    generated = []
    for i, screenshot in enumerate(screenshots):
        print(f"[{i+1}/{len(screenshots)}] Processing {screenshot.name}...")
        output_path = output_dir / f"{screenshot.stem}_mockup.png"

        # Use base colors if specified, otherwise extract from each screenshot
        colors = base_colors if base_colors else resolve_colors(screenshot_path=str(screenshot))

        result = quick_mockup(
            screenshot_path=str(screenshot),
            output_path=str(output_path),
            background_style=args.style,
            device=args.device,
            colors=colors,
            platform=args.platform
        )
        generated.append(result)

    print(f"\nGenerated {len(generated)} mockups in {output_dir}")
    for path in generated:
        print(f"  - {path}")

    return 0


def cmd_github(args):
    """Full pipeline: Clone GitHub repo → Build → Capture → Generate mockups."""
    print(f"\nGitHub to Mockup Pipeline")
    print(f"Repository: {args.repo}")
    print(f"Style: {args.style}")
    print()

    pipeline = GitHubMockupPipeline(
        github_url=args.repo,
        output_dir=args.output or "./output",
        device=args.device
    )

    outputs = pipeline.run(
        background_style=args.style,
        screenshot_count=args.count,
        scheme=args.scheme,
        simulator_device=args.simulator,
        cleanup_after=args.cleanup
    )

    if outputs:
        print("\nGenerated mockups:")
        for output in outputs:
            print(f"  - {output.mockup_path}")
        return 0
    else:
        print("\nNo mockups generated. Check the output above for errors.")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Generate beautiful social media mockups from GitHub projects",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Screenshot command
    screenshot_parser = subparsers.add_parser(
        "screenshot",
        help="Generate mockup from a screenshot"
    )
    screenshot_parser.add_argument("screenshot", help="Path to screenshot image")
    screenshot_parser.add_argument("-o", "--output", help="Output path for mockup")
    screenshot_parser.add_argument(
        "-s", "--style",
        choices=["mesh", "soft", "aurora", "glass", "sunset", "ocean", "gradient", "flowing", "waves", "expand"],
        default="mesh",
        help="Background style (default: flowing)"
    )
    screenshot_parser.add_argument(
        "-d", "--device",
        default="iphone_17_pro_max",
        help="Device frame to use"
    )
    screenshot_parser.add_argument(
        "-c", "--colors",
        help="Color palette: preset name (sunset, ocean, etc.) or hex codes (#FF5733,#3498DB)"
    )
    screenshot_parser.add_argument(
        "-p", "--platform",
        choices=["twitter", "twitter4", "instagram", "square", "story", "wide"],
        help="Platform preset for optimal sizing (twitter, twitter4, instagram, etc.)"
    )
    screenshot_parser.set_defaults(func=cmd_screenshot)

    # Video command
    video_parser = subparsers.add_parser(
        "video",
        help="Generate video mockup from a screen recording"
    )
    video_parser.add_argument("video", help="Path to screen recording video")
    video_parser.add_argument("-o", "--output", help="Output video path")
    video_parser.add_argument(
        "-s", "--style",
        choices=["mesh", "soft", "aurora", "glass", "sunset", "ocean", "gradient", "expand"],
        default="expand",
        help="Background style (default: expand)"
    )
    video_parser.add_argument(
        "-p", "--platform",
        choices=["twitter", "instagram", "square", "story", "wide"],
        default="twitter",
        help="Platform preset (default: twitter)"
    )
    video_parser.add_argument(
        "-c", "--colors",
        help="Color palette: preset name or hex codes"
    )
    video_parser.set_defaults(func=cmd_video)

    # Project command
    project_parser = subparsers.add_parser(
        "project",
        help="Generate mockups from a project directory"
    )
    project_parser.add_argument("project", help="Path to project directory")
    project_parser.add_argument("-o", "--output", help="Output directory for mockups")
    project_parser.add_argument(
        "-s", "--style",
        choices=["mesh", "soft", "aurora", "glass", "sunset", "ocean", "gradient", "flowing", "waves", "expand"],
        default="mesh",
        help="Background style"
    )
    project_parser.add_argument(
        "-d", "--device",
        default="iphone_17_pro_max",
        help="Device frame to use"
    )
    project_parser.add_argument(
        "--capture",
        action="store_true",
        help="Capture new screenshots from simulator"
    )
    project_parser.add_argument(
        "-n", "--count",
        type=int,
        default=3,
        help="Number of screenshots to capture/use"
    )
    project_parser.set_defaults(func=cmd_project)
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a project without generating mockups"
    )
    analyze_parser.add_argument("project", help="Path to project directory")
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Styles command
    styles_parser = subparsers.add_parser(
        "styles",
        help="Show available background styles"
    )
    styles_parser.set_defaults(func=cmd_styles)

    # Colors command
    colors_parser = subparsers.add_parser(
        "colors",
        help="Show available color palettes"
    )
    colors_parser.set_defaults(func=cmd_colors)

    # Platforms command
    platforms_parser = subparsers.add_parser(
        "platforms",
        help="Show available platform presets"
    )
    platforms_parser.set_defaults(func=cmd_platforms)

    # Batch command (folder of screenshots)
    batch_parser = subparsers.add_parser(
        "batch",
        help="Generate mockups from all screenshots in a folder"
    )
    batch_parser.add_argument("folder", help="Folder containing screenshots")
    batch_parser.add_argument("-o", "--output", help="Output directory (default: folder/mockups)")
    batch_parser.add_argument(
        "-s", "--style",
        choices=["mesh", "soft", "aurora", "glass", "sunset", "ocean", "gradient", "flowing", "waves", "expand"],
        default="mesh",
        help="Background style"
    )
    batch_parser.add_argument(
        "-d", "--device",
        default="iphone_17_pro_max",
        help="Device frame to use"
    )
    batch_parser.add_argument(
        "-c", "--colors",
        help="Color palette: preset name (sunset, ocean, etc.) or hex codes (#FF5733,#3498DB)"
    )
    batch_parser.add_argument(
        "-p", "--platform",
        choices=["twitter", "twitter4", "instagram", "square", "story", "wide"],
        help="Platform preset for optimal sizing (twitter, twitter4, instagram, etc.)"
    )
    batch_parser.set_defaults(func=cmd_batch)

    # GitHub command (full pipeline)
    github_parser = subparsers.add_parser(
        "github",
        help="Clone repo, build, capture screenshots, generate mockups"
    )
    github_parser.add_argument(
        "repo",
        help="GitHub repo (owner/repo or full URL)"
    )
    github_parser.add_argument("-o", "--output", help="Output directory for mockups")
    github_parser.add_argument(
        "-s", "--style",
        choices=["mesh", "soft", "aurora", "glass", "sunset", "ocean", "gradient", "flowing", "waves", "expand"],
        default="mesh",
        help="Background style"
    )
    github_parser.add_argument(
        "-d", "--device",
        default="iphone_17_pro_max",
        help="Device frame to use"
    )
    github_parser.add_argument(
        "-n", "--count",
        type=int,
        default=3,
        help="Number of screenshots to capture"
    )
    github_parser.add_argument(
        "--scheme",
        help="Xcode scheme to build (auto-detected if not specified)"
    )
    github_parser.add_argument(
        "--simulator",
        default="iPhone 17 Pro Max",
        help="iOS Simulator device name"
    )
    github_parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete cloned repo after completion"
    )
    github_parser.set_defaults(func=cmd_github)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
