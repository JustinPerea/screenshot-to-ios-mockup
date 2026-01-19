"""
Main pipeline orchestrator for GitHub-to-Social.
Coordinates project analysis, screenshot capture, and mockup generation.
"""

from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime

from .analysis.project_analyzer import ProjectAnalyzer, ProjectInfo
from .analysis.color_extractor import ColorExtractor
from .capture.ios_simulator import IOSSimulatorCapture
from .mockup.composer import MockupComposer
from .github.cloner import GitHubCloner, CloneResult
from .github.analyzer import GitHubAnalyzer, GitHubProjectInfo


@dataclass
class MockupOutput:
    """Output from the mockup generation pipeline."""
    mockup_path: str
    screenshot_path: str
    background_style: str
    colors_used: List[tuple]
    project_info: ProjectInfo


class GitHubToSocialPipeline:
    """
    Main pipeline for generating social media content from GitHub projects.
    
    Flow:
    1. Analyze project (type, colors, features)
    2. Find or capture screenshots
    3. Generate beautiful mockups
    4. (Future) Generate captions
    5. (Future) Post to social media
    """
    
    def __init__(self,
                 project_path: str = None,
                 github_repo: str = None,
                 output_dir: str = None,
                 device: str = "iphone_17_pro_max"):
        self.project_path = Path(project_path) if project_path else None
        self.github_repo = github_repo
        self.output_dir = Path(output_dir) if output_dir else Path("./output")
        self.device = device
        
        # Initialize components
        self.analyzer = ProjectAnalyzer(
            project_path=str(self.project_path) if self.project_path else None,
            github_repo=github_repo
        )
        self.composer = MockupComposer(device=device)
        
        # iOS capture (only if local project)
        self.ios_capture = None
        if self.project_path:
            self.ios_capture = IOSSimulatorCapture(
                project_path=str(self.project_path),
                output_dir=str(self.output_dir / "screenshots")
            )
    
    def run(self,
            background_style: str = "flowing",
            capture_screenshots: bool = True,
            screenshot_count: int = 3) -> List[MockupOutput]:
        """
        Run the full pipeline.
        
        Args:
            background_style: Style for mockup backgrounds
            capture_screenshots: Whether to capture new screenshots if none exist
            screenshot_count: Number of screenshots to capture
        
        Returns:
            List of generated mockup outputs
        """
        outputs = []
        
        # 1. Analyze project
        print("Analyzing project...")
        project_info = self.analyzer.analyze()
        print(f"  Type: {project_info.type}")
        print(f"  Name: {project_info.name}")
        print(f"  Language: {project_info.language}")
        
        # 2. Get screenshots
        screenshots = self._get_screenshots(
            project_info,
            capture_new=capture_screenshots,
            count=screenshot_count
        )
        
        if not screenshots:
            print("No screenshots available. Please provide screenshots or enable capture.")
            return outputs
        
        print(f"Found {len(screenshots)} screenshots")
        
        # 3. Generate mockups for each screenshot
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, screenshot_path in enumerate(screenshots):
            print(f"Generating mockup {i + 1}/{len(screenshots)}...")
            
            output = self._generate_single_mockup(
                screenshot_path=screenshot_path,
                project_info=project_info,
                background_style=background_style,
                index=i
            )
            outputs.append(output)
        
        # 4. Generate multi-device mockup if multiple screenshots
        if len(screenshots) >= 2:
            print("Generating multi-device mockup...")
            multi_output = self._generate_multi_mockup(
                screenshots[:3],  # Use up to 3
                project_info,
                background_style
            )
            outputs.append(multi_output)
        
        print(f"\nGenerated {len(outputs)} mockups in {self.output_dir}")
        return outputs
    
    def _get_screenshots(self,
                        project_info: ProjectInfo,
                        capture_new: bool,
                        count: int) -> List[str]:
        """Get screenshots - either existing or newly captured."""
        screenshots = []
        
        # Check for existing screenshots
        if project_info.has_existing_screenshots and project_info.screenshots_path:
            screenshot_dir = Path(project_info.screenshots_path)
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                screenshots.extend([str(p) for p in screenshot_dir.glob(ext)])
        
        # If no existing screenshots and capture is enabled
        if not screenshots and capture_new:
            if project_info.type == 'ios' and self.ios_capture:
                try:
                    print("Capturing screenshots from iOS Simulator...")
                    screenshots = self.ios_capture.full_capture_flow(
                        screenshot_count=count
                    )
                except Exception as e:
                    print(f"Failed to capture screenshots: {e}")
        
        return screenshots[:count]  # Limit to requested count
    
    def _generate_single_mockup(self,
                               screenshot_path: str,
                               project_info: ProjectInfo,
                               background_style: str,
                               index: int) -> MockupOutput:
        """Generate a single mockup from a screenshot."""
        # Extract colors if not in project info
        colors = project_info.colors
        if not colors:
            extractor = ColorExtractor(image_path=screenshot_path)
            colors = extractor.get_complementary_colors()
        
        # Generate mockup
        mockup = self.composer.create_mockup(
            screenshot_path=screenshot_path,
            background_style=background_style,
            custom_colors=colors if colors else None
        )
        
        # Save mockup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"mockup_{project_info.name}_{index + 1}_{timestamp}.png"
        output_path = self.output_dir / output_filename
        
        self.composer.save(mockup, str(output_path))
        
        return MockupOutput(
            mockup_path=str(output_path),
            screenshot_path=screenshot_path,
            background_style=background_style,
            colors_used=colors,
            project_info=project_info
        )
    
    def _generate_multi_mockup(self,
                              screenshots: List[str],
                              project_info: ProjectInfo,
                              background_style: str) -> MockupOutput:
        """Generate a multi-device mockup."""
        mockup = self.composer.create_multi_device_mockup(
            screenshots=screenshots,
            background_style=background_style,
            layout="stacked"
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"mockup_{project_info.name}_multi_{timestamp}.png"
        output_path = self.output_dir / output_filename
        
        self.composer.save(mockup, str(output_path))
        
        return MockupOutput(
            mockup_path=str(output_path),
            screenshot_path=screenshots[0],  # Primary screenshot
            background_style=background_style,
            colors_used=project_info.colors,
            project_info=project_info
        )
    
    def generate_from_screenshot(self,
                                screenshot_path: str,
                                background_style: str = "flowing",
                                output_name: str = None) -> str:
        """
        Quick method to generate a mockup from a single screenshot.
        Useful for manual/CLI usage.
        
        Returns:
            Path to generated mockup
        """
        mockup = self.composer.create_mockup(
            screenshot_path=screenshot_path,
            background_style=background_style
        )
        
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"mockup_{timestamp}.png"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / output_name
        
        self.composer.save(mockup, str(output_path))
        return str(output_path)


def quick_mockup(screenshot_path: str,
                output_path: str = None,
                background_style: str = "mesh",
                device: str = "iphone_17_pro_max",
                colors: list = None,
                platform: str = None) -> str:
    """
    Quick function to generate a mockup from a screenshot.

    Args:
        screenshot_path: Path to the screenshot image
        output_path: Where to save the mockup (optional)
        background_style: 'mesh', 'soft', 'aurora', 'glass', 'sunset', 'ocean', 'expand', etc.
        device: Device frame to use
        colors: Custom color palette (list of RGB tuples) or None for auto-extract
        platform: Platform preset ('twitter', 'instagram', 'square', 'story', 'wide')

    Returns:
        Path to the generated mockup
    """
    composer = MockupComposer(device=device, platform=platform)
    mockup = composer.create_mockup(
        screenshot_path=screenshot_path,
        background_style=background_style,
        custom_colors=colors
    )

    if not output_path:
        screenshot = Path(screenshot_path)
        output_path = screenshot.parent / f"{screenshot.stem}_mockup.png"

    composer.save(mockup, output_path)
    return output_path


class GitHubMockupPipeline:
    """
    Full pipeline: GitHub URL → Clone → Build → Capture → Mockup

    This is the main entry point for generating mockups directly from a GitHub repo.
    """

    def __init__(self,
                 github_url: str,
                 output_dir: str = None,
                 workspace_dir: str = None,
                 device: str = "iphone_17_pro_max"):
        """
        Initialize the GitHub mockup pipeline.

        Args:
            github_url: GitHub repository URL or owner/repo format
            output_dir: Where to save generated mockups
            workspace_dir: Where to clone repos (default: ./repos)
            device: Device frame to use for mockups
        """
        self.github_url = github_url
        self.output_dir = Path(output_dir) if output_dir else Path("./output")
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path("./repos")
        self.device = device

        # Initialize components
        self.cloner = GitHubCloner(workspace_dir=str(self.workspace_dir))
        self.composer = MockupComposer(device=device)

        # Will be set after cloning
        self.local_path: Optional[Path] = None
        self.project_info: Optional[GitHubProjectInfo] = None
        self.ios_capture: Optional[IOSSimulatorCapture] = None

    def run(self,
            background_style: str = "flowing",
            screenshot_count: int = 3,
            scheme: str = None,
            simulator_device: str = "iPhone 17 Pro Max",
            cleanup_after: bool = False) -> List[MockupOutput]:
        """
        Run the full pipeline.

        Args:
            background_style: Style for mockup backgrounds
            screenshot_count: Number of screenshots to capture
            scheme: Xcode scheme to build (auto-detected if not specified)
            simulator_device: iOS Simulator device name
            cleanup_after: Whether to delete cloned repo after completion

        Returns:
            List of generated mockup outputs
        """
        outputs = []

        try:
            # Step 1: Clone the repository
            print(f"\n{'='*60}")
            print("Step 1: Cloning repository...")
            print(f"{'='*60}")

            clone_result = self.cloner.clone(self.github_url)

            if not clone_result.success:
                print(f"Failed to clone: {clone_result.error}")
                return outputs

            self.local_path = Path(clone_result.local_path)
            print(f"Cloned to: {self.local_path}")

            # Step 2: Analyze the project
            print(f"\n{'='*60}")
            print("Step 2: Analyzing project...")
            print(f"{'='*60}")

            analyzer = GitHubAnalyzer.from_local(str(self.local_path))
            self.project_info = analyzer.analyze_local(str(self.local_path))

            print(f"  Name: {self.project_info.name}")
            print(f"  Type: {self.project_info.project_type}")
            print(f"  Has iOS: {self.project_info.has_ios}")
            print(f"  Has Web: {self.project_info.has_web}")
            print(f"  Colors found: {len(self.project_info.brand_colors)}")

            if self.project_info.description:
                print(f"  Description: {self.project_info.description[:100]}...")

            # Step 3: Capture screenshots
            print(f"\n{'='*60}")
            print("Step 3: Capturing screenshots...")
            print(f"{'='*60}")

            screenshots = self._capture_screenshots(
                scheme=scheme,
                simulator_device=simulator_device,
                count=screenshot_count
            )

            if not screenshots:
                print("No screenshots captured. Cannot generate mockups.")
                return outputs

            print(f"Captured {len(screenshots)} screenshots")

            # Step 4: Generate mockups
            print(f"\n{'='*60}")
            print("Step 4: Generating mockups...")
            print(f"{'='*60}")

            self.output_dir.mkdir(parents=True, exist_ok=True)

            for i, screenshot_path in enumerate(screenshots):
                print(f"  Generating mockup {i + 1}/{len(screenshots)}...")
                output = self._generate_mockup(
                    screenshot_path=screenshot_path,
                    background_style=background_style,
                    index=i
                )
                outputs.append(output)

            # Generate multi-device mockup if we have multiple screenshots
            if len(screenshots) >= 2:
                print("  Generating multi-device mockup...")
                multi_output = self._generate_multi_mockup(
                    screenshots[:3],
                    background_style
                )
                outputs.append(multi_output)

            print(f"\n{'='*60}")
            print(f"Complete! Generated {len(outputs)} mockups")
            print(f"{'='*60}")
            for output in outputs:
                print(f"  - {output.mockup_path}")

            return outputs

        finally:
            if cleanup_after and self.local_path:
                self.cloner.cleanup(self.local_path.name)

    def _capture_screenshots(self,
                            scheme: str = None,
                            simulator_device: str = "iPhone 17 Pro Max",
                            count: int = 3) -> List[str]:
        """Capture screenshots from the project."""
        screenshots = []

        # Check for existing screenshots first
        existing = self._find_existing_screenshots()
        if existing:
            print(f"Found {len(existing)} existing screenshots in repo")
            return existing[:count]

        # Try iOS capture if it's an iOS project
        if self.project_info and self.project_info.has_ios:
            ios_path = self.project_info.ios_path or str(self.local_path / "ios")

            print(f"iOS project detected at: {ios_path}")

            self.ios_capture = IOSSimulatorCapture(
                project_path=ios_path,
                device_name=simulator_device,
                output_dir=str(self.output_dir / "screenshots")
            )

            try:
                screenshots = self.ios_capture.full_capture_flow(
                    scheme=scheme,
                    screenshot_count=count
                )
            except Exception as e:
                print(f"iOS capture failed: {e}")
                print("You may need to:")
                print("  - Open Xcode and resolve any signing issues")
                print("  - Ensure the scheme name is correct")
                print("  - Check that CocoaPods/SPM dependencies are installed")

        # TODO: Add web capture with Playwright
        # if self.project_info and self.project_info.has_web:
        #     ...

        return screenshots

    def _find_existing_screenshots(self) -> List[str]:
        """Find any existing screenshots in the repo."""
        if not self.local_path:
            return []

        screenshot_dirs = [
            'screenshots', 'Screenshots',
            'assets/screenshots', 'docs/screenshots',
            'fastlane/screenshots', 'metadata/screenshots'
        ]

        for dir_name in screenshot_dirs:
            dir_path = self.local_path / dir_name
            if dir_path.exists():
                screenshots = []
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    screenshots.extend([str(p) for p in dir_path.glob(ext)])
                if screenshots:
                    return screenshots

        return []

    def _generate_mockup(self,
                        screenshot_path: str,
                        background_style: str,
                        index: int) -> MockupOutput:
        """Generate a single mockup."""
        # Use brand colors if available
        colors = self.project_info.brand_colors if self.project_info else None

        if not colors:
            extractor = ColorExtractor(image_path=screenshot_path)
            colors = extractor.get_complementary_colors()

        mockup = self.composer.create_mockup(
            screenshot_path=screenshot_path,
            background_style=background_style,
            custom_colors=colors if colors else None
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = self.project_info.name if self.project_info else "project"
        output_filename = f"mockup_{name}_{index + 1}_{timestamp}.png"
        output_path = self.output_dir / output_filename

        self.composer.save(mockup, str(output_path))

        # Create a minimal ProjectInfo for compatibility
        project_info = ProjectInfo(
            name=name,
            type=self.project_info.project_type if self.project_info else "unknown",
            language=self.project_info.language if self.project_info else "unknown",
            description=self.project_info.description if self.project_info else None,
            colors=colors,
            screenshots_path=None,
            has_existing_screenshots=False,
            key_features=[],
            recent_changes=[]
        )

        return MockupOutput(
            mockup_path=str(output_path),
            screenshot_path=screenshot_path,
            background_style=background_style,
            colors_used=colors,
            project_info=project_info
        )

    def _generate_multi_mockup(self,
                              screenshots: List[str],
                              background_style: str) -> MockupOutput:
        """Generate a multi-device mockup."""
        mockup = self.composer.create_multi_device_mockup(
            screenshots=screenshots,
            background_style=background_style,
            layout="stacked"
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = self.project_info.name if self.project_info else "project"
        output_filename = f"mockup_{name}_multi_{timestamp}.png"
        output_path = self.output_dir / output_filename

        self.composer.save(mockup, str(output_path))

        colors = self.project_info.brand_colors if self.project_info else []

        project_info = ProjectInfo(
            name=name,
            type=self.project_info.project_type if self.project_info else "unknown",
            language=self.project_info.language if self.project_info else "unknown",
            description=self.project_info.description if self.project_info else None,
            colors=colors,
            screenshots_path=None,
            has_existing_screenshots=False,
            key_features=[],
            recent_changes=[]
        )

        return MockupOutput(
            mockup_path=str(output_path),
            screenshot_path=screenshots[0],
            background_style=background_style,
            colors_used=colors,
            project_info=project_info
        )


def github_to_mockup(github_url: str,
                     output_dir: str = None,
                     background_style: str = "flowing",
                     screenshot_count: int = 3,
                     scheme: str = None) -> List[str]:
    """
    Convenience function: GitHub URL → Mockups

    Args:
        github_url: GitHub repo URL or owner/repo format
        output_dir: Where to save mockups
        background_style: Background style for mockups
        screenshot_count: Number of screenshots to capture
        scheme: Xcode scheme (auto-detected if not specified)

    Returns:
        List of paths to generated mockups
    """
    pipeline = GitHubMockupPipeline(
        github_url=github_url,
        output_dir=output_dir
    )

    outputs = pipeline.run(
        background_style=background_style,
        screenshot_count=screenshot_count,
        scheme=scheme
    )

    return [o.mockup_path for o in outputs]
