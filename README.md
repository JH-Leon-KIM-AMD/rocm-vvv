# rocm-vvv

A comprehensive ROCm ecosystem **V**ersion **V**erification and **V**isualization tool with colorful terminal output.

## Author

**JeongHyun Kim**

## Description

`rocm-vvv` (ROCm Version Verification & Visualization) is a powerful tool that searches for and displays versions of various ROCm components installed on your system.

### Why "vvv"?
- **V**ersion - Check versions of all ROCm components
- **V**erification - Verify your ROCm installation
- **V**isualization - Visualize results with colorful output

## Components Checked

### Essential Components (Simple Mode)
- ROCm base version
- HIP (Heterogeneous-Compute Interface for Portability)
- hipBLAS and MIOpen
- rocBLAS, rocFFT, rocSPARSE, rocRAND
- ROCm SMI and AMDGPU driver
- HIPCC compiler

### Extended Components (Full Mode)
**Core Math Libraries:**
- Tensile, hipSPARSE, rocALUTION, rocSOLVER
- hipSOLVER, hipFFT, rocSPARSELt

**Performance & Tools:**
- rocPROFILER, rocTRACER, rocm-cmake

**Parallel Primitives:**
- hipCUB, rocWMMA, rocPRIM, rocTHRUST

**ML/AI Libraries:**
- AMDMIGraphX, hipTensor

**Media Libraries:**
- rocDecode, rocJPEG, rocAL, MIVisionX

**Development Tools:**
- AOMP, ROCdbgapi, ROCgdb

**Additional Components:**
- Composable Kernel (CK), RCCL, rocminfo, hipBLASLt

## Installation

```bash
pip install rocm-vvv
```

## Usage

### Basic Usage

After installation, you can run the tool using:

```bash
rocm-vvv
```

Or use the ultra-short alias:

```bash
rvvv
```

### Search Modes

The tool supports two search modes:

#### Simple Mode (Default)
Checks essential ROCm components (11 components):
```bash
rocm-vvv --mode simple
```

#### Full Mode
Checks all ROCm components including extended libraries (38+ components):
```bash
rocm-vvv --mode full
```

### Additional Options

```bash
# Disable progress bar
rocm-vvv --no-progress

# Full mode with progress bar
rocm-vvv --mode full

# Get help
rocm-vvv --help

# Show version
rocm-vvv --version
```

For more comprehensive results (may require sudo):

```bash
sudo rocm-vvv --mode full
```

## Example Output

```
╔═══════════════════════════════════════════════════════════╗
║           ROCm Ecosystem Version Checker                  ║
║                                                           ║
║  Searching for ROCm components across the system...       ║
╚═══════════════════════════════════════════════════════════╝

============================================================
                      GPU Information                       
============================================================
  GPU 0: AMD Radeon RX 6800 XT

============================================================
                  ROCm Component Versions                   
============================================================
  AMDGPU Driver     : 6.3.6 (/sys/module/amdgpu/version)
  Composable Kernel : Found (version in header) (/opt/rocm-6.4.1/include/ck/ck.hpp)
  MIOpen            : 3.4.1 (/opt/rocm-6.4.1/include/miopen/version.h)
  ROCm              : 6.4.1 (/opt/rocm-6.4.1/.info/version)
  ROCm SMI          : ROCM-SMI version: 3.0.0+e68c0d1 (rocm-smi command)
  hipBLAS           : 2.4.0 (/opt/rocm-6.4.1/include/hipblas/hipblas-version.h)
  hipBLASLt         : 6.4.1 (/opt/rocm-6.4.1/lib/libhipblaslt.so.6.4.1)
  rocRAND           : 6.4.1 (/opt/rocm-6.4.1/lib/librocrand.so.6.4.1)
  rocSPARSE         : 3.4.0 (/opt/rocm-6.4.1/include/rocsparse/rocsparse-version.h)

============================================================
                        Summary                             
============================================================
  Components found: 9/9

============================================================
                        References                          
============================================================
  Tool Repository: https://github.com/JH-Leon-KIM-AMD/rocm-vvv
  Author: JeongHyun Kim (jeonghyun.kim@amd.com)
  PyPI Package: https://pypi.org/project/rocm-vvv/
```

*Sample output from a real ROCm 6.4.1 installation*

## Requirements

- Python 3.6 or higher
- Linux operating system
- ROCm installation (for detecting components)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Issues

If you encounter any problems, please file an issue at:
https://github.com/JH-Leon-KIM-AMD/rocm-vvv/issues
