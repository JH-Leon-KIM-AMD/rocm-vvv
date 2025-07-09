"""
Tests for rocm-vvv
Author: JeongHyun Kim
"""

import unittest
from rocm_vvv import check_rocm_version, check_gpu_info


class TestROCmVVV(unittest.TestCase):
    def test_check_rocm_version_returns_dict(self):
        """Test that check_rocm_version returns a dictionary"""
        result = check_rocm_version()
        self.assertIsInstance(result, dict)
    
    def test_check_gpu_info_returns_dict(self):
        """Test that check_gpu_info returns a dictionary"""
        result = check_gpu_info()
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main()
