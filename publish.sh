#!/bin/bash
set -e

echo "🚀 ROCm-VVV PyPI Publishing Script"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -f "rocm_vvv/__init__.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
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

# Update version in pyproject.toml
sed -i.bak "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

echo "🧹 Cleaning up previous builds..."
rm -rf build/ dist/ *.egg-info/

# Clean up backup files
rm -f setup.py.bak rocm_vvv/__init__.py.bak rocm_vvv/checker.py.bak pyproject.toml.bak

echo ""
echo "✅ Version updated to $VERSION!"
echo ""

# Ask for automatic git operations
read -p "🚀 Do you want to automatically commit, tag, and push? (Y/n): " AUTO_PUSH
AUTO_PUSH=${AUTO_PUSH:-Y}  # Default to Y if empty

if [[ $AUTO_PUSH =~ ^[Yy]$ ]]; then
    echo ""
    echo "📦 Committing changes..."
    git add .
    git commit -m "Bump version to $VERSION" || {
        echo "❌ Error: Failed to commit. Please check if there are any issues."
        exit 1
    }
    
    echo "🏷️  Creating tag v$VERSION..."
    git tag "v$VERSION"
    
    echo "📤 Pushing to GitHub..."
    git push origin main || {
        echo "❌ Error: Failed to push to main branch. Please check your connection."
        exit 1
    }
    
    echo "📤 Pushing tag..."
    git push origin "v$VERSION" || {
        echo "❌ Error: Failed to push tag. Please check your connection."
        exit 1
    }
    
    echo ""
    echo "✅ All done! Version $VERSION has been pushed to GitHub."
    echo ""
    echo "🚀 GitHub Actions is now building and publishing to PyPI!"
    echo "   Check progress at: https://github.com/JH-Leon-KIM-AMD/rocm-vvv/actions"
    echo ""
    echo "📦 Package will be available at: https://pypi.org/project/rocm-vvv/$VERSION/"
    echo ""
else
    echo ""
    echo "📌 Manual steps to publish:"
    echo "───────────────────────────────────────"
    echo "git add ."
    echo "git commit -m \"Bump version to $VERSION\""
    echo "git tag v$VERSION"
    echo "git push origin main"
    echo "git push origin v$VERSION"
    echo "───────────────────────────────────────"
    echo ""
    echo "🚀 GitHub Actions will automatically build and publish to PyPI!"
    echo "   Check progress at: https://github.com/JH-Leon-KIM-AMD/rocm-vvv/actions"
    echo ""
fi