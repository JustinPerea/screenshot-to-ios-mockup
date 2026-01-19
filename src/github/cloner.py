"""
GitHub repository cloner.
Clones repos locally for building and screenshot capture.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import re


@dataclass
class CloneResult:
    """Result of a clone operation."""
    success: bool
    local_path: Optional[str]
    repo_name: str
    error: Optional[str] = None


class GitHubCloner:
    """
    Clones GitHub repositories for local processing.
    Handles both HTTPS and SSH URLs, as well as owner/repo format.
    """
    
    def __init__(self, workspace_dir: str = None):
        """
        Initialize the cloner.
        
        Args:
            workspace_dir: Directory to clone repos into. Defaults to ./repos/
        """
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path("./repos")
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    def clone(self, 
              repo: str, 
              branch: str = None,
              shallow: bool = True,
              force: bool = False) -> CloneResult:
        """
        Clone a GitHub repository.
        
        Args:
            repo: Repository identifier. Can be:
                  - "owner/repo" format
                  - Full HTTPS URL
                  - Full SSH URL
            branch: Specific branch to clone (optional)
            shallow: If True, do a shallow clone (faster, less disk space)
            force: If True, delete existing clone and re-clone
        
        Returns:
            CloneResult with success status and local path
        """
        # Parse the repo identifier
        repo_url, repo_name = self._parse_repo(repo)
        
        if not repo_url:
            return CloneResult(
                success=False,
                local_path=None,
                repo_name=repo,
                error=f"Could not parse repository: {repo}"
            )
        
        local_path = self.workspace_dir / repo_name
        
        # Handle existing clone
        if local_path.exists():
            if force:
                print(f"Removing existing clone: {local_path}")
                shutil.rmtree(local_path)
            else:
                # Pull latest instead of re-cloning
                print(f"Repository already cloned, pulling latest...")
                pull_result = self._pull(local_path, branch)
                if pull_result:
                    return CloneResult(
                        success=True,
                        local_path=str(local_path),
                        repo_name=repo_name
                    )
                # If pull failed, try fresh clone
                shutil.rmtree(local_path)
        
        # Build clone command
        cmd = ["git", "clone"]
        
        if shallow:
            cmd.extend(["--depth", "1"])
        
        if branch:
            cmd.extend(["--branch", branch])
        
        cmd.extend([repo_url, str(local_path)])
        
        print(f"Cloning: {repo_url}")
        print(f"To: {local_path}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                return CloneResult(
                    success=False,
                    local_path=None,
                    repo_name=repo_name,
                    error=result.stderr
                )
            
            return CloneResult(
                success=True,
                local_path=str(local_path),
                repo_name=repo_name
            )
            
        except subprocess.TimeoutExpired:
            return CloneResult(
                success=False,
                local_path=None,
                repo_name=repo_name,
                error="Clone operation timed out"
            )
        except Exception as e:
            return CloneResult(
                success=False,
                local_path=None,
                repo_name=repo_name,
                error=str(e)
            )
    
    def _parse_repo(self, repo: str) -> tuple[Optional[str], str]:
        """
        Parse a repository identifier into URL and name.
        
        Returns:
            Tuple of (clone_url, repo_name)
        """
        # Already a full URL
        if repo.startswith("https://"):
            # Extract repo name from URL
            match = re.search(r'github\.com/([^/]+/[^/]+?)(?:\.git)?$', repo)
            if match:
                full_name = match.group(1)
                repo_name = full_name.split('/')[-1]
                # Ensure .git suffix for cloning
                if not repo.endswith('.git'):
                    repo = repo + '.git'
                return repo, repo_name
            return None, repo
        
        # SSH URL
        if repo.startswith("git@"):
            match = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$', repo)
            if match:
                full_name = match.group(1)
                repo_name = full_name.split('/')[-1]
                return repo, repo_name
            return None, repo
        
        # owner/repo format
        if '/' in repo and not repo.startswith('/'):
            parts = repo.split('/')
            if len(parts) == 2:
                owner, name = parts
                url = f"https://github.com/{owner}/{name}.git"
                return url, name
        
        return None, repo
    
    def _pull(self, local_path: Path, branch: str = None) -> bool:
        """Pull latest changes in an existing repo."""
        try:
            # Fetch
            subprocess.run(
                ["git", "fetch", "--all"],
                cwd=local_path,
                capture_output=True,
                timeout=60
            )
            
            # Reset to origin
            target = f"origin/{branch}" if branch else "origin/HEAD"
            result = subprocess.run(
                ["git", "reset", "--hard", target],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def cleanup(self, repo_name: str = None):
        """
        Clean up cloned repositories.
        
        Args:
            repo_name: Specific repo to clean up. If None, cleans all.
        """
        if repo_name:
            repo_path = self.workspace_dir / repo_name
            if repo_path.exists():
                shutil.rmtree(repo_path)
                print(f"Cleaned up: {repo_path}")
        else:
            if self.workspace_dir.exists():
                shutil.rmtree(self.workspace_dir)
                self.workspace_dir.mkdir(parents=True, exist_ok=True)
                print(f"Cleaned up all repos in: {self.workspace_dir}")
    
    def list_cloned(self) -> list[str]:
        """List all cloned repositories."""
        if not self.workspace_dir.exists():
            return []
        
        return [
            d.name for d in self.workspace_dir.iterdir() 
            if d.is_dir() and (d / ".git").exists()
        ]
