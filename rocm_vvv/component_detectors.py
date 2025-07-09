#!/usr/bin/env python3
"""
Component detection classes for ROCm ecosystem components
"""

import os
import subprocess
import re
import glob
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional


class ComponentDetector(ABC):
    """Abstract base class for component detectors"""
    
    def __init__(self, name: str, search_dirs: List[str]):
        self.name = name
        self.search_dirs = search_dirs
    
    @abstractmethod
    def detect(self) -> Optional[str]:
        """Detect the component version and return version string with path"""
        pass
    
    def run_command(self, cmd: List[str]) -> Optional[str]:
        """Run command and return output"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
    
    def find_file_version(self, pattern: str) -> Optional[Tuple[str, str]]:
        """Search for files matching pattern and extract version"""
        for search_dir in self.search_dirs:
            for file_path in glob.glob(os.path.join(search_dir, pattern), recursive=True):
                if os.path.isfile(file_path):
                    version_match = re.search(r'(\d+\.\d+\.\d+(?:\.\d+)?)', file_path)
                    if version_match:
                        return version_match.group(1), file_path
        return None
    
    def read_file_for_version(self, file_path: str, pattern: str) -> Optional[Tuple[str, str]]:
        """Read file and search for version pattern"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    return match.group(1), file_path
        except:
            pass
        return None


class ROCmDetector(ComponentDetector):
    """Detector for ROCm base version"""
    
    def detect(self) -> Optional[str]:
        # Check /opt/rocm/.info/version
        for rocm_dir in glob.glob("/opt/rocm*"):
            version_file = os.path.join(rocm_dir, ".info", "version")
            if os.path.exists(version_file):
                result = self.read_file_for_version(version_file, r'^(\d+\.\d+\.\d+)')
                if result:
                    version, found_path = result
                    return f"{version} ({found_path})"
        
        # Alternative: rocm-core package
        output = self.run_command(['dpkg', '-l', 'rocm-core'])
        if output:
            match = re.search(r'rocm-core\s+(\d+\.\d+\.\d+)', output)
            if match:
                return f"{match.group(1)} (dpkg package)"
        
        return None


class HIPDetector(ComponentDetector):
    """Detector for HIP version"""
    
    def detect(self) -> Optional[str]:
        # Try hipconfig command
        hip_version = self.run_command(['hipconfig', '--version'])
        if hip_version:
            return f"{hip_version} (hipconfig command)"
        
        # Try to find hip version from headers
        for d in self.search_dirs:
            hip_version_file = os.path.join(d, "include", "hip", "hip_version.h")
            if os.path.exists(hip_version_file):
                result = self.read_file_for_version(hip_version_file, 
                    r'#define\s+HIP_VERSION\s+(\d+)')
                if result:
                    version, found_path = result
                    # Convert to readable format (e.g., 50300000 -> 5.3.0)
                    major = int(version) // 10000000
                    minor = (int(version) // 100000) % 100
                    patch = (int(version) // 100) % 1000
                    return f"{major}.{minor}.{patch} ({found_path})"
        
        return None


class HeaderBasedDetector(ComponentDetector):
    """Generic detector for components with version headers"""
    
    def __init__(self, name: str, search_dirs: List[str], header_path: str, 
                 major_define: str, minor_define: str, patch_define: str):
        super().__init__(name, search_dirs)
        self.header_path = header_path
        self.major_define = major_define
        self.minor_define = minor_define
        self.patch_define = patch_define
    
    def detect(self) -> Optional[str]:
        for d in self.search_dirs:
            version_file = os.path.join(d, self.header_path)
            if os.path.exists(version_file):
                major_result = self.read_file_for_version(version_file, self.major_define)
                minor_result = self.read_file_for_version(version_file, self.minor_define)
                patch_result = self.read_file_for_version(version_file, self.patch_define)
                
                if major_result and minor_result and patch_result:
                    major, found_path = major_result
                    minor, _ = minor_result
                    patch, _ = patch_result
                    return f"{major}.{minor}.{patch} ({found_path})"
        
        return None


class LibraryDetector(ComponentDetector):
    """Generic detector for shared library versions"""
    
    def __init__(self, name: str, search_dirs: List[str], library_pattern: str):
        super().__init__(name, search_dirs)
        self.library_pattern = library_pattern
    
    def detect(self) -> Optional[str]:
        result = self.find_file_version(self.library_pattern)
        if result:
            version, found_path = result
            return f"{version} ({found_path})"
        return None


class CommandDetector(ComponentDetector):
    """Generic detector for command-based versions"""
    
    def __init__(self, name: str, search_dirs: List[str], command: List[str], 
                 version_pattern: str, command_name: str):
        super().__init__(name, search_dirs)
        self.command = command
        self.version_pattern = version_pattern
        self.command_name = command_name
    
    def detect(self) -> Optional[str]:
        output = self.run_command(self.command)
        if output:
            match = re.search(self.version_pattern, output)
            if match:
                return f"{match.group(1)} ({self.command_name} command)"
        return None


class FileContentDetector(ComponentDetector):
    """Generic detector for file content versions"""
    
    def __init__(self, name: str, search_dirs: List[str], file_path: str, 
                 content_pattern: str):
        super().__init__(name, search_dirs)
        self.file_path = file_path
        self.content_pattern = content_pattern
    
    def detect(self) -> Optional[str]:
        if os.path.exists(self.file_path):
            result = self.read_file_for_version(self.file_path, self.content_pattern)
            if result:
                version, found_path = result
                return f"{version} ({found_path})"
        return None


class ComponentDetectorFactory:
    """Factory for creating component detectors"""
    
    @staticmethod
    def create_detectors(search_dirs: List[str], mode: str = "simple") -> Dict[str, ComponentDetector]:
        """Create all component detectors based on mode"""
        detectors = {}
        
        # Essential components (simple mode)
        detectors["ROCm"] = ROCmDetector("ROCm", search_dirs)
        detectors["HIP"] = HIPDetector("HIP", search_dirs)
        
        detectors["hipBLAS"] = HeaderBasedDetector(
            "hipBLAS", search_dirs, "include/hipblas/hipblas-version.h",
            r'#define\s+hipblasVersionMajor\s+(\d+)',
            r'#define\s+hipblasVersionMinor\s+(\d+)',
            r'#define\s+hipblasVersionPatch\s+(\d+)'
        )
        
        detectors["MIOpen"] = HeaderBasedDetector(
            "MIOpen", search_dirs, "include/miopen/version.h",
            r'#define\s+MIOPEN_VERSION_MAJOR\s+(\d+)',
            r'#define\s+MIOPEN_VERSION_MINOR\s+(\d+)',
            r'#define\s+MIOPEN_VERSION_PATCH\s+(\d+)'
        )
        
        detectors["rocBLAS"] = HeaderBasedDetector(
            "rocBLAS", search_dirs, "include/rocblas/rocblas-version.h",
            r'#define\s+ROCBLAS_VERSION_MAJOR\s+(\d+)',
            r'#define\s+ROCBLAS_VERSION_MINOR\s+(\d+)',
            r'#define\s+ROCBLAS_VERSION_PATCH\s+(\d+)'
        )
        
        detectors["rocFFT"] = LibraryDetector("rocFFT", search_dirs, "**/librocfft.so*")
        detectors["rocSPARSE"] = HeaderBasedDetector(
            "rocSPARSE", search_dirs, "include/rocsparse/rocsparse-version.h",
            r'#define\s+ROCSPARSE_VERSION_MAJOR\s+(\d+)',
            r'#define\s+ROCSPARSE_VERSION_MINOR\s+(\d+)',
            r'#define\s+ROCSPARSE_VERSION_PATCH\s+(\d+)'
        )
        
        detectors["rocRAND"] = LibraryDetector("rocRAND", search_dirs, "**/librocrand.so*")
        detectors["ROCm SMI"] = CommandDetector(
            "ROCm SMI", search_dirs, ['rocm-smi', '--version'],
            r'ROCM-SMI version: ([^\s]+)', "rocm-smi"
        )
        
        detectors["AMDGPU Driver"] = FileContentDetector(
            "AMDGPU Driver", search_dirs, '/sys/module/amdgpu/version', r'(.+)'
        )
        
        detectors["HIPCC"] = CommandDetector(
            "HIPCC", search_dirs, ['hipcc', '--version'],
            r'HIP version: (\d+\.\d+\.\d+)', "hipcc"
        )
        
        # Extended components (full mode)
        if mode == "full":
            detectors["hipBLASLt"] = LibraryDetector("hipBLASLt", search_dirs, "**/libhipblaslt.so*")
            detectors["Composable Kernel"] = ComponentDetectorFactory._create_ck_detector(search_dirs)
            detectors["rocminfo"] = CommandDetector(
                "rocminfo", search_dirs, ['rocminfo', '--support'],
                r'.*', "rocminfo"
            )
            detectors["rocPRIM"] = ComponentDetectorFactory._create_rocprim_detector(search_dirs)
            detectors["rocTHRUST"] = ComponentDetectorFactory._create_rocthrust_detector(search_dirs)
            detectors["RCCL"] = HeaderBasedDetector(
                "RCCL", search_dirs, "include/rccl/rccl.h",
                r'#define\s+NCCL_MAJOR\s+(\d+)',
                r'#define\s+NCCL_MINOR\s+(\d+)',
                r'#define\s+NCCL_PATCH\s+(\d+)'
            )
            
            # Add more extended components...
            detectors.update(ComponentDetectorFactory._create_extended_detectors(search_dirs))
        
        return detectors
    
    @staticmethod
    def _create_ck_detector(search_dirs: List[str]) -> ComponentDetector:
        """Create Composable Kernel detector"""
        class CKDetector(ComponentDetector):
            def detect(self) -> Optional[str]:
                for d in self.search_dirs:
                    ck_path = os.path.join(d, "include", "ck", "ck.hpp")
                    if os.path.exists(ck_path):
                        return f"Found (version in header) ({ck_path})"
                return None
        
        return CKDetector("Composable Kernel", search_dirs)
    
    @staticmethod
    def _create_rocprim_detector(search_dirs: List[str]) -> ComponentDetector:
        """Create rocPRIM detector"""
        class RocPRIMDetector(ComponentDetector):
            def detect(self) -> Optional[str]:
                result = self.find_file_version("**/rocprim/include/rocprim/rocprim_version.hpp")
                if result:
                    _, found_path = result
                    return f"Found ({found_path})"
                return None
        
        return RocPRIMDetector("rocPRIM", search_dirs)
    
    @staticmethod
    def _create_rocthrust_detector(search_dirs: List[str]) -> ComponentDetector:
        """Create rocTHRUST detector"""
        class RocTHRUSTDetector(ComponentDetector):
            def detect(self) -> Optional[str]:
                for d in self.search_dirs:
                    thrust_path = os.path.join(d, "include", "rocthrust", "thrust", "version.h")
                    if os.path.exists(thrust_path):
                        return f"Found ({thrust_path})"
                return None
        
        return RocTHRUSTDetector("rocTHRUST", search_dirs)
    
    @staticmethod
    def _create_extended_detectors(search_dirs: List[str]) -> Dict[str, ComponentDetector]:
        """Create extended component detectors"""
        detectors = {}
        
        # Core Math Libraries
        detectors["Tensile"] = LibraryDetector("Tensile", search_dirs, "**/Tensile/Source/lib/libtensile.so*")
        detectors["hipSPARSE"] = HeaderBasedDetector(
            "hipSPARSE", search_dirs, "include/hipsparse/hipsparse-version.h",
            r'#define\s+hipsparseVersionMajor\s+(\d+)',
            r'#define\s+hipsparseVersionMinor\s+(\d+)',
            r'#define\s+hipsparseVersionPatch\s+(\d+)'
        )
        detectors["rocALUTION"] = LibraryDetector("rocALUTION", search_dirs, "**/librocalution.so*")
        detectors["rocSOLVER"] = HeaderBasedDetector(
            "rocSOLVER", search_dirs, "include/rocsolver/rocsolver-version.h",
            r'#define\s+ROCSOLVER_VERSION_MAJOR\s+(\d+)',
            r'#define\s+ROCSOLVER_VERSION_MINOR\s+(\d+)',
            r'#define\s+ROCSOLVER_VERSION_PATCH\s+(\d+)'
        )
        detectors["hipSOLVER"] = LibraryDetector("hipSOLVER", search_dirs, "**/libhipsolver.so*")
        detectors["hipFFT"] = HeaderBasedDetector(
            "hipFFT", search_dirs, "include/hipfft/hipfft-version.h",
            r'#define\s+HIPFFT_VERSION_MAJOR\s+(\d+)',
            r'#define\s+HIPFFT_VERSION_MINOR\s+(\d+)',
            r'#define\s+HIPFFT_VERSION_PATCH\s+(\d+)'
        )
        detectors["rocSPARSELt"] = LibraryDetector("rocSPARSELt", search_dirs, "**/librocsparselt.so*")
        
        # Performance & Tools
        detectors["rocPROFILER"] = LibraryDetector("rocPROFILER", search_dirs, "**/librocprofiler.so*")
        detectors["rocTRACER"] = LibraryDetector("rocTRACER", search_dirs, "**/libroctracer.so*")
        
        # Parallel Primitives
        detectors["hipCUB"] = HeaderBasedDetector(
            "hipCUB", search_dirs, "include/hipcub/hipcub_version.hpp",
            r'#define\s+HIPCUB_VERSION_MAJOR\s+(\d+)',
            r'#define\s+HIPCUB_VERSION_MINOR\s+(\d+)',
            r'#define\s+HIPCUB_VERSION_PATCH\s+(\d+)'
        )
        detectors["rocWMMA"] = LibraryDetector("rocWMMA", search_dirs, "**/librocwmma.so*")
        
        # ML/AI Libraries
        detectors["AMDMIGraphX"] = LibraryDetector("AMDMIGraphX", search_dirs, "**/libmigraphx.so*")
        detectors["hipTensor"] = LibraryDetector("hipTensor", search_dirs, "**/libhiptensor.so*")
        
        # Media Libraries
        detectors["rocDecode"] = LibraryDetector("rocDecode", search_dirs, "**/librocdecode.so*")
        detectors["rocJPEG"] = LibraryDetector("rocJPEG", search_dirs, "**/librocjpeg.so*")
        detectors["rocAL"] = LibraryDetector("rocAL", search_dirs, "**/librocal.so*")
        detectors["MIVisionX"] = LibraryDetector("MIVisionX", search_dirs, "**/libmivisionx.so*")
        
        # Development Tools
        detectors["AOMP"] = CommandDetector(
            "AOMP", search_dirs, ['aomp', '--version'],
            r'version\s+(\d+\.\d+\.\d+)', "aomp"
        )
        detectors["ROCdbgapi"] = LibraryDetector("ROCdbgapi", search_dirs, "**/librocdbgapi.so*")
        detectors["ROCgdb"] = CommandDetector(
            "ROCgdb", search_dirs, ['rocgdb', '--version'],
            r'GNU gdb.*?(\d+\.\d+)', "rocgdb"
        )
        
        return detectors