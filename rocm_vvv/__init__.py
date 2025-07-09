"""
rocm-vvv: ROCm Version Verification & Visualization
Author: JeongHyun Kim
A comprehensive ROCm ecosystem version checker with colorful output
"""

__version__ = "0.0.8"
__author__ = "JeongHyun Kim"
__email__ = "jeonghyun.kim@amd.com"

from .checker import main, ROCmVersionChecker, GPUDetector

__all__ = ['main', 'ROCmVersionChecker', 'GPUDetector']
