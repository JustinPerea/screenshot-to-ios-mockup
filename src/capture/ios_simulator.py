"""
iOS Simulator screenshot capture.
Builds and runs iOS apps in the simulator to capture screenshots.
"""

import subprocess
import json
import time
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class SimulatorDevice:
    """Represents an iOS Simulator device."""
    udid: str
    name: str
    state: str
    runtime: str
    is_available: bool


class IOSSimulatorCapture:
    """
    Capture screenshots from iOS Simulator.
    Handles building, launching, and capturing screenshots from iOS apps.
    """
    
    def __init__(self,
                 project_path: str,
                 device_name: str = "iPhone 17 Pro Max",
                 output_dir: str = None):
        self.project_path = Path(project_path).resolve()  # Convert to absolute path
        self.device_name = device_name
        self.output_dir = Path(output_dir).resolve() if output_dir else self.project_path / "screenshots"
        self._device = None
    
    def get_available_devices(self) -> List[SimulatorDevice]:
        """Get list of available simulator devices."""
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "-j"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to list devices: {result.stderr}")
        
        data = json.loads(result.stdout)
        devices = []
        
        for runtime, device_list in data.get("devices", {}).items():
            for device in device_list:
                devices.append(SimulatorDevice(
                    udid=device["udid"],
                    name=device["name"],
                    state=device["state"],
                    runtime=runtime,
                    is_available=device.get("isAvailable", False)
                ))
        
        return devices
    
    def find_device(self, name: str = None) -> Optional[SimulatorDevice]:
        """Find a simulator device by name."""
        target_name = name or self.device_name
        devices = self.get_available_devices()
        
        # Prefer available devices
        for device in devices:
            if target_name.lower() in device.name.lower() and device.is_available:
                return device
        
        # Fall back to any matching device
        for device in devices:
            if target_name.lower() in device.name.lower():
                return device
        
        return None
    
    def boot_simulator(self, device: SimulatorDevice = None) -> SimulatorDevice:
        """Boot the simulator if not already running."""
        device = device or self.find_device()
        
        if not device:
            raise RuntimeError(f"Could not find device: {self.device_name}")
        
        if device.state != "Booted":
            result = subprocess.run(
                ["xcrun", "simctl", "boot", device.udid],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 and "already booted" not in result.stderr.lower():
                raise RuntimeError(f"Failed to boot simulator: {result.stderr}")
            
            # Wait for boot
            time.sleep(3)
        
        self._device = device
        return device
    
    def shutdown_simulator(self, device: SimulatorDevice = None) -> None:
        """Shutdown the simulator."""
        device = device or self._device
        if device:
            subprocess.run(
                ["xcrun", "simctl", "shutdown", device.udid],
                capture_output=True
            )
    
    def detect_project_type(self) -> Dict:
        """Detect the type of iOS project and build settings."""
        project_info = {
            "type": None,
            "project_file": None,
            "workspace_file": None,
            "scheme": None
        }
        
        # Check for workspace (common with CocoaPods/SPM)
        workspaces = list(self.project_path.glob("*.xcworkspace"))
        if workspaces:
            project_info["workspace_file"] = workspaces[0]
            project_info["type"] = "workspace"
        
        # Check for project file
        projects = list(self.project_path.glob("*.xcodeproj"))
        if projects:
            project_info["project_file"] = projects[0]
            if not project_info["type"]:
                project_info["type"] = "project"
        
        # Try to detect scheme
        if project_info["project_file"]:
            scheme_path = project_info["project_file"] / "xcshareddata" / "xcschemes"
            if scheme_path.exists():
                schemes = list(scheme_path.glob("*.xcscheme"))
                if schemes:
                    project_info["scheme"] = schemes[0].stem
        
        # Fallback: use project name as scheme
        if not project_info["scheme"]:
            if project_info["project_file"]:
                project_info["scheme"] = project_info["project_file"].stem
        
        return project_info
    
    def build_app(self, 
                 scheme: str = None,
                 configuration: str = "Debug") -> str:
        """
        Build the iOS app for simulator.
        
        Returns:
            Path to the built .app bundle
        """
        project_info = self.detect_project_type()
        scheme = scheme or project_info.get("scheme")
        
        if not scheme:
            raise RuntimeError("Could not detect scheme. Please provide scheme name.")
        
        device = self.find_device()
        if not device:
            raise RuntimeError(f"Could not find device: {self.device_name}")
        
        # Build command
        cmd = ["xcodebuild"]
        
        if project_info.get("workspace_file"):
            cmd.extend(["-workspace", str(project_info["workspace_file"])])
        elif project_info.get("project_file"):
            cmd.extend(["-project", str(project_info["project_file"])])
        else:
            raise RuntimeError("No Xcode project or workspace found")
        
        cmd.extend([
            "-scheme", scheme,
            "-configuration", configuration,
            "-destination", f"platform=iOS Simulator,id={device.udid}",
            "-derivedDataPath", str(self.project_path / "build"),
            "CODE_SIGN_IDENTITY=-",
            "CODE_SIGNING_REQUIRED=NO",
            "CODE_SIGNING_ALLOWED=NO",
            "build"
        ])
        
        print(f"Building: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_path
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Build failed: {result.stderr}")
        
        # Find the built app
        build_dir = self.project_path / "build" / "Build" / "Products" / f"{configuration}-iphonesimulator"
        apps = list(build_dir.glob("*.app"))
        
        if not apps:
            raise RuntimeError("Could not find built app bundle")
        
        return str(apps[0])
    
    def install_app(self, app_path: str, device: SimulatorDevice = None) -> None:
        """Install an app on the simulator."""
        device = device or self._device or self.find_device()
        
        result = subprocess.run(
            ["xcrun", "simctl", "install", device.udid, app_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to install app: {result.stderr}")
    
    def launch_app(self, bundle_id: str, device: SimulatorDevice = None) -> None:
        """Launch an app on the simulator."""
        device = device or self._device or self.find_device()
        
        result = subprocess.run(
            ["xcrun", "simctl", "launch", device.udid, bundle_id],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to launch app: {result.stderr}")
    
    def capture_screenshot(self, 
                          filename: str = None,
                          device: SimulatorDevice = None) -> str:
        """
        Capture a screenshot from the simulator.
        
        Returns:
            Path to the captured screenshot
        """
        device = device or self._device or self.find_device()
        
        if not device:
            raise RuntimeError("No simulator device available")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
        
        output_path = self.output_dir / filename
        
        result = subprocess.run(
            ["xcrun", "simctl", "io", device.udid, "screenshot", str(output_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to capture screenshot: {result.stderr}")
        
        return str(output_path)
    
    def capture_sequence(self,
                        count: int = 3,
                        delay: float = 2.0,
                        prefix: str = "screen") -> List[str]:
        """
        Capture a sequence of screenshots.
        
        Args:
            count: Number of screenshots to capture
            delay: Delay between captures in seconds
            prefix: Filename prefix
        
        Returns:
            List of screenshot paths
        """
        screenshots = []
        
        for i in range(count):
            filename = f"{prefix}_{i + 1}.png"
            path = self.capture_screenshot(filename=filename)
            screenshots.append(path)
            
            if i < count - 1:
                time.sleep(delay)
        
        return screenshots
    
    def get_bundle_id_from_app(self, app_path: str) -> str:
        """Extract bundle ID from an app bundle."""
        import plistlib
        
        info_plist = Path(app_path) / "Info.plist"
        
        if not info_plist.exists():
            raise RuntimeError(f"Info.plist not found in {app_path}")
        
        with open(info_plist, 'rb') as f:
            plist = plistlib.load(f)
        
        return plist.get("CFBundleIdentifier", "")
    
    def full_capture_flow(self,
                         scheme: str = None,
                         screenshot_count: int = 3,
                         delay: float = 3.0) -> List[str]:
        """
        Complete flow: build, install, launch, and capture screenshots.
        
        Returns:
            List of captured screenshot paths
        """
        # Boot simulator
        device = self.boot_simulator()
        print(f"Booted simulator: {device.name}")
        
        try:
            # Build app
            print("Building app...")
            app_path = self.build_app(scheme=scheme)
            print(f"Built: {app_path}")
            
            # Get bundle ID
            bundle_id = self.get_bundle_id_from_app(app_path)
            print(f"Bundle ID: {bundle_id}")
            
            # Install app
            print("Installing app...")
            self.install_app(app_path)
            
            # Launch app
            print("Launching app...")
            self.launch_app(bundle_id)
            
            # Wait for app to fully launch
            time.sleep(3)
            
            # Capture screenshots
            print(f"Capturing {screenshot_count} screenshots...")
            screenshots = self.capture_sequence(
                count=screenshot_count,
                delay=delay
            )
            
            print(f"Captured: {screenshots}")
            return screenshots
            
        finally:
            # Optionally shutdown
            pass  # Keep simulator running for inspection
