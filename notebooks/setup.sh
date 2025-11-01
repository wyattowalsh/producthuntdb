#!/bin/bash
# ProductHuntDB Kaggle Notebook Setup Script
# This script handles installation and configuration for both Kaggle and local environments

set -e  # Exit on error

echo "🚀 ProductHuntDB Setup Script"
echo "================================"

# Detect environment
if [ -d "/kaggle/working" ]; then
    ENVIRONMENT="kaggle"
    WORKING_DIR="/kaggle/working"
    echo "📍 Environment: Kaggle Notebook"
else
    ENVIRONMENT="local"
    WORKING_DIR=$(pwd)
    echo "📍 Environment: Local Development"
fi

# Install ProductHuntDB
echo ""
echo "📦 Installing ProductHuntDB..."

if command -v pip &> /dev/null; then
    # Try GitHub installation first
    if pip install -q "git+https://github.com/wyattowalsh/producthuntdb.git" 2>&1; then
        echo "✅ Installed from GitHub"
    else
        # Fallback to PyPI if available
        if pip install -q producthuntdb 2>&1; then
            echo "✅ Installed from PyPI"
        else
            echo "❌ Installation failed. Please install manually:"
            echo "   pip install git+https://github.com/wyattowalsh/producthuntdb.git"
            exit 1
        fi
    fi
else
    echo "❌ pip not found. Please install Python and pip first."
    exit 1
fi

# Install notebook dependencies
echo ""
echo "📦 Installing notebook dependencies..."
if pip install -q plotly kaleido 2>&1; then
    echo "✅ Installed plotly and kaleido"
else
    echo "⚠️  Optional dependencies failed to install (non-critical)"
fi

# Set up paths
echo ""
echo "🔧 Configuring paths..."
export DB_PATH="${WORKING_DIR}/producthunt.db"
export EXPORT_DIR="${WORKING_DIR}/export"

echo "   Database: ${DB_PATH}"
echo "   Export: ${EXPORT_DIR}"

# Load secrets from Kaggle if available
if [ "$ENVIRONMENT" = "kaggle" ]; then
    echo ""
    echo "🔐 Kaggle Secrets will be loaded in notebook cells"
    echo "   Required: PRODUCTHUNT_TOKEN"
    echo "   Optional: KAGGLE_USERNAME, KAGGLE_KEY, KAGGLE_DATASET_SLUG"
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."
if python -c "import producthuntdb" 2>&1; then
    echo "✅ producthuntdb module imported successfully"
else
    echo "❌ Failed to import producthuntdb"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Configure PRODUCTHUNT_TOKEN in Kaggle Secrets"
echo "  2. Run: producthuntdb init"
echo "  3. Run: producthuntdb verify"
echo "  4. Run: producthuntdb sync"
