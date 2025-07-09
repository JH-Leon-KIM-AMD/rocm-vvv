#!/usr/bin/env python3
"""
ROCm Ecosystem Version Checker - Refactored Version
Searches for and displays versions of various ROCm components with colorful output
"""

import os
import subprocess
import re
import glob
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from .component_detectors import ComponentDetectorFactory


# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ProgressBar:
    """Progress bar utility"""
    
    def __init__(self, total: int, bar_length: int = 40):
        self.total = total
        self.current = 0
        self.bar_length = bar_length
    
    def update(self, description: str = ""):
        """Update progress bar"""
        if self.total == 0:
            return
        
        progress = self.current / self.total
        filled_length = int(self.bar_length * progress)
        bar = '█' * filled_length + '░' * (self.bar_length - filled_length)
        percentage = int(progress * 100)
        
        print(f"\r{Colors.CYAN}[{bar}] {percentage}% {description}{Colors.ENDC}", end='', flush=True)
        if self.current == self.total:
            print()  # New line when complete
        
        self.current += 1


class OutputFormatter:
    """Output formatting utility"""
    
    @staticmethod
    def print_colored(text: str, color: str = Colors.ENDC, end: str = '\n') -> None:
        """Print text with color"""
        print(f"{color}{text}{Colors.ENDC}", end=end)
    
    @staticmethod
    def print_header(text: str) -> None:
        """Print section header"""
        OutputFormatter.print_colored(f"\n{'='*60}", Colors.CYAN)
        OutputFormatter.print_colored(f"{text:^60}", Colors.BOLD + Colors.CYAN)
        OutputFormatter.print_colored(f"{'='*60}\n", Colors.CYAN)
    
    @staticmethod
    def print_banner(mode: str, component_count: int) -> None:
        """Print application banner"""
        mode_text = "Essential Components" if mode == "simple" else "All Components"
        
        OutputFormatter.print_colored(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║           ROCm Ecosystem Version Checker                  ║
    ║                                                           ║
    ║  Mode: {mode_text:<45} ║
    ║  Components: {component_count:<42} ║
    ║  Searching for ROCm components across the system...       ║
    ╚═══════════════════════════════════════════════════════════╝
    """, Colors.BOLD + Colors.CYAN)


class GPUDetector:
    """GPU information detector"""
    
    @staticmethod
    def run_command(cmd: List[str]) -> Optional[str]:
        """Run command and return output"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
    
    @staticmethod
    def detect_gpus() -> Dict[str, str]:
        """Get GPU information"""
        gpu_info = {}
        
        # Try rocm-smi
        output = GPUDetector.run_command(['rocm-smi', '--showproductname'])
        if output:
            lines = output.strip().split('\n')
            for i, line in enumerate(lines):
                if 'Card series' in line:
                    gpu_info[f'GPU {i}'] = line.split(':')[-1].strip()
        
        # Alternative: check lspci
        if not gpu_info:
            output = GPUDetector.run_command(['lspci'])
            if output:
                # Look for AMD GPUs (VGA or Display controller)
                amd_gpus = [line for line in output.split('\n') 
                           if 'AMD' in line and ('VGA' in line or 'Display' in line)]
                for i, gpu in enumerate(amd_gpus):
                    gpu_info[f'GPU {i}'] = gpu.split(':', 2)[-1].strip()
        
        # Try to check /sys/class/drm for AMD GPUs
        if not gpu_info:
            try:
                drm_cards = glob.glob('/sys/class/drm/card*/device/vendor')
                amd_cards = []
                for vendor_file in drm_cards:
                    with open(vendor_file, 'r') as f:
                        vendor_id = f.read().strip()
                        if vendor_id == '0x1002':  # AMD vendor ID
                            card_path = os.path.dirname(vendor_file)
                            device_file = os.path.join(card_path, 'device')
                            if os.path.exists(device_file):
                                with open(device_file, 'r') as df:
                                    device_id = df.read().strip()
                                    amd_cards.append(f"AMD GPU [Vendor: {vendor_id}, Device: {device_id}]")
                
                for i, card in enumerate(amd_cards):
                    gpu_info[f'GPU {i}'] = card
            except:
                pass
        
        return gpu_info


class ROCmVersionChecker:
    """Main ROCm version checker"""
    
    def __init__(self):
        self.search_dirs = self._get_search_dirs()
    
    def _get_search_dirs(self) -> List[str]:
        """Get search directories"""
        search_dirs = [
            "/opt/rocm*",
            "/usr",
            "/usr/local",
            "/usr/lib",
            "/usr/lib64",
            "/usr/share",
            "/etc",
            os.path.expanduser("~/.local"),
        ]
        
        # Expand wildcards
        expanded_dirs = []
        for d in search_dirs:
            if '*' in d:
                expanded_dirs.extend(glob.glob(d))
            else:
                expanded_dirs.append(d)
        
        return expanded_dirs
    
    def check_components(self, mode: str = "simple", show_progress: bool = True) -> Dict[str, Optional[str]]:
        """Check versions of ROCm components"""
        # Create detectors
        detectors = ComponentDetectorFactory.create_detectors(self.search_dirs, mode)
        
        # Initialize results
        versions = {name: None for name in detectors.keys()}
        
        # Setup progress bar
        progress_bar = ProgressBar(len(detectors)) if show_progress else None
        
        # Check each component
        for name, detector in detectors.items():
            if progress_bar:
                progress_bar.update(f"Checking {name}...")
            
            try:
                version = detector.detect()
                if version:
                    versions[name] = version
            except Exception as e:
                # Log error but continue
                pass
        
        return versions
    
    def display_results(self, versions: Dict[str, Optional[str]], mode: str) -> None:
        """Display results"""
        # Display GPU info
        OutputFormatter.print_header("GPU Information")
        gpu_info = GPUDetector.detect_gpus()
        if gpu_info:
            for gpu, name in gpu_info.items():
                OutputFormatter.print_colored(f"  {gpu}: ", Colors.GREEN, end='')
                OutputFormatter.print_colored(name, Colors.BOLD)
        else:
            OutputFormatter.print_colored("  No AMD GPUs detected", Colors.RED)
        
        # Display component versions
        OutputFormatter.print_header("ROCm Component Versions")
        if versions:
            max_name_len = max(len(name) for name in versions.keys())
            for component, version in sorted(versions.items()):
                if version:
                    OutputFormatter.print_colored(f"  {component:<{max_name_len}} : ", Colors.GREEN, end='')
                    OutputFormatter.print_colored(version, Colors.BOLD + Colors.YELLOW)
                else:
                    OutputFormatter.print_colored(f"  {component:<{max_name_len}} : ", Colors.RED, end='')
                    OutputFormatter.print_colored("Not found", Colors.RED)
        else:
            OutputFormatter.print_colored("  No ROCm components found!", Colors.RED)
        
        # Display summary
        OutputFormatter.print_header("Summary")
        found_count = sum(1 for v in versions.values() if v)
        total_count = len(versions)
        
        OutputFormatter.print_colored(f"  Components found: {found_count}/{total_count}", 
                     Colors.GREEN if found_count > 0 else Colors.RED)
        
        if found_count < total_count:
            OutputFormatter.print_colored("\n  Missing components might not be installed or", Colors.YELLOW)
            OutputFormatter.print_colored("  might be in non-standard locations.", Colors.YELLOW)
            OutputFormatter.print_colored("\n  Try running with sudo for more complete results.", Colors.CYAN)
        
        # Display references
        OutputFormatter.print_header("References")
        OutputFormatter.print_colored("  Tool Repository: ", Colors.GREEN, end='')
        OutputFormatter.print_colored("https://github.com/JH-Leon-KIM-AMD/rocm-vvv", Colors.BOLD + Colors.CYAN)

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ROCm Ecosystem Version Checker')
    parser.add_argument('--mode', choices=['simple', 'full'], default='simple',
                        help='Search mode: simple (essential components) or full (all components)')
    parser.add_argument('--no-progress', action='store_true',
                        help='Disable progress bar')
    parser.add_argument('--version', action='version', version='rocm-vvv 0.0.5')
    
    args = parser.parse_args()
    
    # Create checker
    checker = ROCmVersionChecker()
    
    # Display banner
    detectors = ComponentDetectorFactory.create_detectors(checker.search_dirs, args.mode)
    OutputFormatter.print_banner(args.mode, len(detectors))
    
    # Check components
    versions = checker.check_components(mode=args.mode, show_progress=not args.no_progress)
    
    # Display results
    checker.display_results(versions, args.mode)


if __name__ == "__main__":
    main()