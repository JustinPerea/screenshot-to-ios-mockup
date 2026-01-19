"""
Project analyzer - understands repositories to make intelligent decisions
about what to screenshot and how to present it.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import re


@dataclass
class ProjectInfo:
    """Information about a project."""
    name: str
    type: str  # 'ios', 'android', 'web', 'cli', 'library', 'unknown'
    language: str
    description: Optional[str]
    colors: List[Tuple[int, int, int]]
    screenshots_path: Optional[str]
    has_existing_screenshots: bool
    key_features: List[str]
    recent_changes: List[str]


class ProjectAnalyzer:
    """
    Analyzes projects to understand what they are and how to present them.
    Works with both local paths and GitHub repositories.
    """
    
    # File patterns that indicate project type
    PROJECT_INDICATORS = {
        'ios': [
            '*.xcodeproj', '*.xcworkspace', 'Package.swift',
            'Podfile', 'Cartfile', '*.swift'
        ],
        'android': [
            'build.gradle', 'settings.gradle', 'AndroidManifest.xml',
            '*.kt', 'gradlew'
        ],
        'web': [
            'package.json', 'index.html', 'next.config.js', 
            'nuxt.config.js', 'vite.config.js', 'webpack.config.js'
        ],
        'cli': [
            'Cargo.toml', 'go.mod', 'setup.py', 'pyproject.toml'
        ],
    }
    
    # Common screenshot locations
    SCREENSHOT_PATHS = [
        'screenshots', 'Screenshots', 'assets/screenshots',
        'docs/screenshots', 'images', 'docs/images',
        'fastlane/screenshots', 'metadata/screenshots'
    ]
    
    # Color extraction from common config files
    COLOR_SOURCES = {
        'ios': ['Assets.xcassets/*/Contents.json', '*.xcassets/AccentColor.colorset/Contents.json'],
        'web': ['tailwind.config.js', 'tailwind.config.ts', 'theme.json', 'styles/variables.css'],
    }
    
    def __init__(self, project_path: str = None, github_repo: str = None):
        self.project_path = Path(project_path) if project_path else None
        self.github_repo = github_repo  # format: "owner/repo"
    
    def analyze(self) -> ProjectInfo:
        """Analyze the project and return structured information."""
        if self.project_path:
            return self._analyze_local()
        elif self.github_repo:
            return self._analyze_github()
        else:
            raise ValueError("Either project_path or github_repo must be provided")
    
    def _analyze_local(self) -> ProjectInfo:
        """Analyze a local project directory."""
        project_type = self._detect_project_type()
        language = self._detect_language(project_type)
        name = self._get_project_name()
        description = self._get_description()
        colors = self._extract_colors(project_type)
        screenshots_path = self._find_screenshots()
        features = self._extract_features()
        
        return ProjectInfo(
            name=name,
            type=project_type,
            language=language,
            description=description,
            colors=colors,
            screenshots_path=screenshots_path,
            has_existing_screenshots=screenshots_path is not None,
            key_features=features,
            recent_changes=[]
        )
    
    def _analyze_github(self) -> ProjectInfo:
        """Analyze a GitHub repository."""
        # This would be called by the agent with GitHub MCP
        # For now, return a placeholder
        return ProjectInfo(
            name=self.github_repo.split('/')[-1] if self.github_repo else "Unknown",
            type="unknown",
            language="unknown",
            description=None,
            colors=[],
            screenshots_path=None,
            has_existing_screenshots=False,
            key_features=[],
            recent_changes=[]
        )
    
    def _detect_project_type(self) -> str:
        """Detect the type of project based on files present."""
        if not self.project_path:
            return "unknown"
        
        for project_type, patterns in self.PROJECT_INDICATORS.items():
            for pattern in patterns:
                matches = list(self.project_path.glob(f"**/{pattern}"))
                if matches:
                    return project_type
        
        return "unknown"
    
    def _detect_language(self, project_type: str) -> str:
        """Detect primary programming language."""
        language_map = {
            'ios': 'Swift',
            'android': 'Kotlin',
            'web': 'TypeScript/JavaScript',
            'cli': 'varies'
        }
        
        if project_type in language_map:
            return language_map[project_type]
        
        # Try to detect from files
        if self.project_path:
            extensions = {}
            for f in self.project_path.rglob("*"):
                if f.is_file() and f.suffix:
                    ext = f.suffix.lower()
                    extensions[ext] = extensions.get(ext, 0) + 1
            
            # Map extensions to languages
            ext_to_lang = {
                '.swift': 'Swift',
                '.kt': 'Kotlin',
                '.java': 'Java',
                '.ts': 'TypeScript',
                '.tsx': 'TypeScript',
                '.js': 'JavaScript',
                '.jsx': 'JavaScript',
                '.py': 'Python',
                '.rs': 'Rust',
                '.go': 'Go',
            }
            
            for ext, lang in ext_to_lang.items():
                if ext in extensions:
                    return lang
        
        return "unknown"
    
    def _get_project_name(self) -> str:
        """Get the project name."""
        if not self.project_path:
            return "Unknown"
        
        # Try package.json
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    if "name" in data:
                        return data["name"]
            except:
                pass
        
        # Try xcodeproj
        xcodeproj = list(self.project_path.glob("*.xcodeproj"))
        if xcodeproj:
            return xcodeproj[0].stem
        
        # Fall back to directory name
        return self.project_path.name
    
    def _get_description(self) -> Optional[str]:
        """Get project description from config files or README."""
        if not self.project_path:
            return None
        
        # Try package.json
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    if "description" in data:
                        return data["description"]
            except:
                pass
        
        # Try README first line/paragraph
        for readme_name in ["README.md", "README.txt", "README"]:
            readme = self.project_path / readme_name
            if readme.exists():
                try:
                    with open(readme) as f:
                        content = f.read()
                        # Get first paragraph after title
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#') and not line.startswith('!'):
                                return line[:200]
                except:
                    pass
        
        return None
    
    def _extract_colors(self, project_type: str) -> List[Tuple[int, int, int]]:
        """Extract brand colors from project configuration."""
        colors = []
        
        if not self.project_path:
            return colors
        
        if project_type == 'ios':
            colors.extend(self._extract_ios_colors())
        elif project_type == 'web':
            colors.extend(self._extract_web_colors())
        
        return colors[:6]  # Limit to 6 colors
    
    def _extract_ios_colors(self) -> List[Tuple[int, int, int]]:
        """Extract colors from iOS asset catalogs."""
        colors = []
        
        # Look for AccentColor
        for asset_path in self.project_path.rglob("AccentColor.colorset/Contents.json"):
            try:
                with open(asset_path) as f:
                    data = json.load(f)
                    for color_data in data.get("colors", []):
                        if "color" in color_data:
                            components = color_data["color"].get("components", {})
                            r = self._parse_color_component(components.get("red", "0"))
                            g = self._parse_color_component(components.get("green", "0"))
                            b = self._parse_color_component(components.get("blue", "0"))
                            colors.append((r, g, b))
            except:
                pass
        
        return colors
    
    def _extract_web_colors(self) -> List[Tuple[int, int, int]]:
        """Extract colors from web project configs."""
        colors = []
        
        # Try tailwind config
        for config_name in ["tailwind.config.js", "tailwind.config.ts"]:
            config_path = self.project_path / config_name
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        content = f.read()
                        # Simple regex for hex colors
                        hex_colors = re.findall(r'["\']#([0-9a-fA-F]{6})["\']', content)
                        for hex_color in hex_colors[:6]:
                            r = int(hex_color[0:2], 16)
                            g = int(hex_color[2:4], 16)
                            b = int(hex_color[4:6], 16)
                            colors.append((r, g, b))
                except:
                    pass
        
        return colors
    
    def _parse_color_component(self, value: str) -> int:
        """Parse an iOS color component value."""
        try:
            if value.startswith("0x"):
                return int(value, 16)
            float_val = float(value)
            if float_val <= 1.0:
                return int(float_val * 255)
            return int(float_val)
        except:
            return 0
    
    def _find_screenshots(self) -> Optional[str]:
        """Find existing screenshots in the project."""
        if not self.project_path:
            return None
        
        for screenshot_dir in self.SCREENSHOT_PATHS:
            path = self.project_path / screenshot_dir
            if path.exists() and path.is_dir():
                # Check if it has image files
                images = list(path.glob("*.png")) + list(path.glob("*.jpg")) + list(path.glob("*.jpeg"))
                if images:
                    return str(path)
        
        return None
    
    def _extract_features(self) -> List[str]:
        """Extract key features from README or other docs."""
        features = []
        
        if not self.project_path:
            return features
        
        # Try README
        for readme_name in ["README.md", "README.txt"]:
            readme = self.project_path / readme_name
            if readme.exists():
                try:
                    with open(readme) as f:
                        content = f.read()
                        # Look for "Features" section
                        features_match = re.search(
                            r'#+\s*Features?\s*\n([\s\S]*?)(?=\n#|\Z)',
                            content,
                            re.IGNORECASE
                        )
                        if features_match:
                            # Extract bullet points
                            bullets = re.findall(r'[-*]\s*(.+)', features_match.group(1))
                            features.extend(bullets[:5])
                except:
                    pass
        
        return features
    
    def get_screenshot_suggestions(self) -> List[str]:
        """
        Suggest which screens/features should be screenshotted.
        Based on project analysis.
        """
        info = self.analyze()
        suggestions = []
        
        # Always suggest main/home screen
        suggestions.append("Main/Home screen")
        
        # Based on project type
        if info.type == 'ios':
            suggestions.extend([
                "Onboarding flow (if present)",
                "Key feature screens",
                "Settings screen",
                "Any unique UI components"
            ])
        elif info.type == 'web':
            suggestions.extend([
                "Landing page",
                "Dashboard (if applicable)",
                "Key feature pages",
                "Mobile responsive view"
            ])
        
        # Based on detected features
        for feature in info.key_features[:3]:
            suggestions.append(f"Feature: {feature}")
        
        return suggestions
