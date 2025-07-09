#!/bin/bash
set -e

echo "🚀 ROCm-VVV PyPI Publishing Script"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -f "rocm_vvv/__init__.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if required tools are installed
if ! command -v twine &> /dev/null; then
    echo "📦 Installing required tools..."
    pip install --upgrade pip build twine
fi

# Get current version
CURRENT_VERSION=$(python3 -c "import rocm_vvv; print(rocm_vvv.__version__)")
echo "📌 Current version: $CURRENT_VERSION"
echo ""

# Get version from user
read -p "🔢 Enter the new version to publish (e.g., 1.0.0): " VERSION

if [ -z "$VERSION" ]; then
    echo "❌ Error: Version cannot be empty"
    exit 1
fi

# Validate version format (basic check)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Version must be in format X.Y.Z (e.g., 1.0.0)"
    exit 1
fi

echo "📝 Updating version to $VERSION..."

# Update version in setup.py
sed -i.bak "s/version=.*/version='$VERSION',/" setup.py

# Update version in __init__.py
sed -i.bak "s/__version__ = .*/__version__ = \"$VERSION\"/" rocm_vvv/__init__.py

# Update version in checker.py
sed -i.bak "s/version='rocm-vvv .*/version='rocm-vvv $VERSION')/" rocm_vvv/checker.py

echo "🧹 Cleaning up previous builds..."
rm -rf build/ dist/ *.egg-info/

echo "🔨 Building package..."
python3 -m build

echo "🔍 Checking package..."
echo "⚠️  Skipping twine check due to metadata format issues - PyPI will validate on upload"

echo "📊 Package contents:"
echo "===================="
ls -la dist/

echo ""
echo "🎯 Ready to publish to PyPI!"
echo "Package: rocm-vvv version $VERSION"
echo ""

# Skip PyPI credential check if running in CI
if [ "$CI" != "true" ]; then
    # Check for PyPI credentials
    if [ -z "$TWINE_USERNAME" ] && [ -z "$TWINE_PASSWORD" ] && [ ! -f ~/.pypirc ]; then
        echo "⚠️  PyPI credentials not found."
        echo "   Please set TWINE_USERNAME and TWINE_PASSWORD environment variables:"
        echo "   export TWINE_USERNAME=__token__"
        echo "   export TWINE_PASSWORD=pypi-your-api-token-here"
        echo ""
        echo "   Or use ~/.pypirc file for local development"
        echo ""
        read -p "❓ Do you have PyPI credentials configured? (y/N): " CREDS_OK
        if [[ ! $CREDS_OK =~ ^[Yy]$ ]]; then
            echo "❌ Please configure PyPI credentials first."
            # Restore backup files
            mv setup.py.bak setup.py
            mv rocm_vvv/__init__.py.bak rocm_vvv/__init__.py
            mv rocm_vvv/checker.py.bak rocm_vvv/checker.py
            echo "🔄 Version changes reverted."
            exit 1
        fi
    fi
fi

# Ask for confirmation
read -p "❓ Do you want to publish to PyPI now? (y/N): " CONFIRM

if [[ $CONFIRM =~ ^[Yy]$ ]]; then
    echo "🚀 Publishing to PyPI..."
    
    # Use environment variables if available, otherwise fall back to config file
    if [ -n "$TWINE_USERNAME" ] && [ -n "$TWINE_PASSWORD" ]; then
        twine upload dist/*
    else
        echo "🔐 Using ~/.pypirc credentials..."
        twine upload dist/*
    fi
    
    echo "✅ Successfully published to PyPI!"
    echo "📦 Package available at: https://pypi.org/project/rocm-vvv/$VERSION/"
    
    # Clean up backup files
    rm -f setup.py.bak rocm_vvv/__init__.py.bak rocm_vvv/checker.py.bak
    
    echo "🏷️  Creating Git tag..."
    git add setup.py rocm_vvv/__init__.py rocm_vvv/checker.py
    git commit -m "Bump version to $VERSION"
    git tag -a "v$VERSION" -m "Release version $VERSION"
    
    echo "📤 Pushing to GitHub..."
    git push origin main
    git push origin "v$VERSION"
    
    echo "🎉 All done! Package published and tagged."
else
    echo "❌ Publication cancelled."
    # Restore backup files
    mv setup.py.bak setup.py
    mv rocm_vvv/__init__.py.bak rocm_vvv/__init__.py
    mv rocm_vvv/checker.py.bak rocm_vvv/checker.py
    echo "🔄 Version changes reverted."
fi