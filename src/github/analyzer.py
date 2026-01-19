"""
GitHub repository analyzer.
Analyzes repos via API/MCP to extract project info, colors, and recent changes.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class GitHubProjectInfo:
    """Information about a GitHub project."""
    owner: str
    repo: str
    name: str
    description: Optional[str]
    language: Optional[str]
    project_type: str  # 'ios', 'web', 'android', 'cli', 'unknown'
    brand_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    recent_commits: List[Dict] = field(default_factory=list)
    has_ios: bool = False
    has_web: bool = False
    ios_path: Optional[str] = None
    web_path: Optional[str] = None
    color_config_path: Optional[str] = None
    screenshots_path: Optional[str] = None


class GitHubAnalyzer:
    """
    Analyzes GitHub repositories to extract project information.
    Can work with:
    - Local cloned repos
    - GitHub API responses (from MCP or direct API)
    """
    
    # Files that indicate project types
    PROJECT_INDICATORS = {
        'ios': ['*.xcodeproj', '*.xcworkspace', 'Package.swift', '*.swift'],
        'web': ['package.json', 'next.config.js', 'next.config.ts', 'vite.config.js'],
        'android': ['build.gradle', 'AndroidManifest.xml', '*.kt'],
    }
    
    # Common color config locations
    COLOR_CONFIGS = [
        'shared/constants/colors.json',
        'src/constants/colors.json',
        'constants/colors.json',
        'tailwind.config.js',
        'tailwind.config.ts',
        'src/styles/theme.json',
    ]
    
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
    
    @classmethod
    def from_url(cls, url: str) -> 'GitHubAnalyzer':
        """Create analyzer from a GitHub URL."""
        # Parse owner/repo from URL
        match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', url)
        if match:
            return cls(match.group(1), match.group(2))
        raise ValueError(f"Could not parse GitHub URL: {url}")
    
    @classmethod
    def from_local(cls, local_path: str) -> 'GitHubAnalyzer':
        """Create analyzer for a local repo (extracts owner/repo from git remote)."""
        import subprocess
        
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=local_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return cls.from_url(result.stdout.strip())
        except Exception:
            pass
        
        # Fallback: use directory name
        path = Path(local_path)
        return cls("local", path.name)
    
    def analyze_from_contents(self, 
                             root_contents: List[Dict],
                             file_fetcher=None) -> GitHubProjectInfo:
        """
        Analyze a repo from its root directory contents.
        
        Args:
            root_contents: List of file/directory dicts from GitHub API
            file_fetcher: Optional callable to fetch file contents
                         Signature: (path: str) -> str
        
        Returns:
            GitHubProjectInfo with extracted information
        """
        info = GitHubProjectInfo(
            owner=self.owner,
            repo=self.repo,
            name=self.repo,
            description=None,
            language=None,
            project_type='unknown'
        )
        
        # Detect project structure
        dir_names = {item['name']: item for item in root_contents if item['type'] == 'dir'}
        file_names = {item['name']: item for item in root_contents if item['type'] == 'file'}
        
        # Check for iOS
        if 'ios' in dir_names:
            info.has_ios = True
            info.ios_path = 'ios'
            info.project_type = 'ios'
        
        # Check for web
        if 'web' in dir_names or 'package.json' in file_names:
            info.has_web = True
            info.web_path = 'web' if 'web' in dir_names else '.'
            if not info.has_ios:
                info.project_type = 'web'
        
        # Check for shared colors config
        if 'shared' in dir_names:
            info.color_config_path = 'shared/constants/colors.json'
        
        # Try to get description from CLAUDE.md or README
        if file_fetcher:
            for doc_file in ['CLAUDE.md', 'README.md']:
                if doc_file in file_names:
                    try:
                        content = file_fetcher(doc_file)
                        desc = self._extract_description(content)
                        if desc:
                            info.description = desc
                            break
                    except Exception:
                        pass
        
        return info
    
    def analyze_local(self, local_path: str) -> GitHubProjectInfo:
        """
        Analyze a locally cloned repository.
        
        Args:
            local_path: Path to the cloned repo
        
        Returns:
            GitHubProjectInfo with extracted information
        """
        path = Path(local_path)
        
        info = GitHubProjectInfo(
            owner=self.owner,
            repo=self.repo,
            name=self.repo,
            description=None,
            language=None,
            project_type='unknown'
        )
        
        # Check for iOS project
        ios_path = path / 'ios'
        if ios_path.exists():
            info.has_ios = True
            info.ios_path = str(ios_path)
            info.project_type = 'ios'
            
            # Find xcodeproj
            xcodeprojs = list(ios_path.glob('*.xcodeproj'))
            if xcodeprojs:
                info.name = xcodeprojs[0].stem
        
        # Check for web project
        web_path = path / 'web'
        if web_path.exists() or (path / 'package.json').exists():
            info.has_web = True
            info.web_path = str(web_path) if web_path.exists() else str(path)
            if not info.has_ios:
                info.project_type = 'web'
        
        # Look for color config
        for color_path in self.COLOR_CONFIGS:
            full_path = path / color_path
            if full_path.exists():
                info.color_config_path = str(full_path)
                info.brand_colors = self._extract_colors_from_file(full_path)
                break
        
        # Get description
        for doc_file in ['CLAUDE.md', 'README.md']:
            doc_path = path / doc_file
            if doc_path.exists():
                try:
                    with open(doc_path, 'r') as f:
                        content = f.read()
                    desc = self._extract_description(content)
                    if desc:
                        info.description = desc
                        break
                except Exception:
                    pass
        
        # Detect language
        info.language = self._detect_language(path)
        
        return info
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract project description from markdown content."""
        # Try to find description in CLAUDE.md format
        match = re.search(r'\*\*Description:\*\*\s*(.+?)(?:\n|$)', content)
        if match:
            return match.group(1).strip()
        
        # Try first paragraph after title
        lines = content.split('\n')
        in_content = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                in_content = True
                continue
            if in_content and not line.startswith('#') and not line.startswith('*') and not line.startswith('-'):
                return line[:200]
        
        return None
    
    def _extract_colors_from_file(self, file_path: Path) -> List[Tuple[int, int, int]]:
        """Extract colors from a color config file."""
        colors = []
        
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                colors = self._extract_colors_from_json(data)
            elif file_path.suffix in ['.js', '.ts']:
                with open(file_path, 'r') as f:
                    content = f.read()
                colors = self._extract_colors_from_js(content)
        except Exception:
            pass
        
        return colors[:6]  # Limit to 6 colors
    
    def _extract_colors_from_json(self, data: dict, prefix: str = '') -> List[Tuple[int, int, int]]:
        """Recursively extract hex colors from JSON data."""
        colors = []
        
        for key, value in data.items():
            if key.startswith('_'):  # Skip comments
                continue
            
            if isinstance(value, str) and value.startswith('#'):
                rgb = self._hex_to_rgb(value)
                if rgb:
                    colors.append(rgb)
            elif isinstance(value, dict):
                colors.extend(self._extract_colors_from_json(value, f"{prefix}{key}."))
        
        return colors
    
    def _extract_colors_from_js(self, content: str) -> List[Tuple[int, int, int]]:
        """Extract hex colors from JavaScript/TypeScript content."""
        colors = []
        hex_pattern = r'["\']#([0-9a-fA-F]{6})["\']'
        
        for match in re.finditer(hex_pattern, content):
            hex_color = match.group(1)
            rgb = self._hex_to_rgb(f"#{hex_color}")
            if rgb:
                colors.append(rgb)
        
        return colors
    
    def _hex_to_rgb(self, hex_color: str) -> Optional[Tuple[int, int, int]]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            try:
                return (
                    int(hex_color[0:2], 16),
                    int(hex_color[2:4], 16),
                    int(hex_color[4:6], 16)
                )
            except ValueError:
                return None
        return None
    
    def _detect_language(self, path: Path) -> Optional[str]:
        """Detect primary programming language."""
        extensions = {}
        
        for f in path.rglob('*'):
            if f.is_file() and f.suffix and not any(p in str(f) for p in ['.git', 'node_modules', 'build', 'Pods']):
                ext = f.suffix.lower()
                extensions[ext] = extensions.get(ext, 0) + 1
        
        ext_to_lang = {
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.py': 'Python',
        }
        
        # Find most common extension that maps to a language
        for ext, count in sorted(extensions.items(), key=lambda x: -x[1]):
            if ext in ext_to_lang:
                return ext_to_lang[ext]
        
        return None
