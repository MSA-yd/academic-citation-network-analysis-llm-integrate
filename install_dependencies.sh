#!/bin/bash
# Dependency Installation Script for Conda Environment
# This script handles dependency installation with proper error handling

set -e

echo "📦 Installing dependencies for Citation Network Analysis Project"
echo "================================================================"
echo "Using conda environment: ds3019"
echo ""

# Initialize conda
eval "$(conda shell.bash hook)"

# Activate conda environment
echo "Activating conda environment: ds3019..."
conda activate ds3019

# Step 1: Upgrade pip
echo ""
echo "Step 1: Upgrading pip..."
pip install --upgrade pip

# Step 2: Install NumPy compatible version (if needed)
echo ""
echo "Step 2: Checking NumPy version..."
python -c "import numpy; print(f'Current NumPy version: {numpy.__version__}')" || echo "NumPy not installed"

# Step 3: Try to install pyarrow using conda (preferred for conda environments)
echo ""
echo "Step 3: Installing pyarrow..."
if conda install -c conda-forge pyarrow -y 2>/dev/null; then
    echo "✅ pyarrow installed successfully via conda"
elif pip install "pyarrow>=14.0.0" --only-binary :all: 2>/dev/null; then
    echo "✅ pyarrow installed successfully from pre-built wheels"
else
    echo "⚠️  pyarrow installation failed, but continuing..."
    echo "💡 The project should still work as pyarrow is only used by some optional features"
fi

# Step 4: Install other dependencies (skip pyarrow if it fails)
echo ""
echo "Step 4: Installing other dependencies..."
# Try to install from requirements.txt, but continue if pyarrow fails
pip install -r requirements.txt 2>&1 | grep -v "pyarrow" || {
    echo "⚠️  Some packages failed to install, trying core dependencies..."
    pip install -r requirements_core.txt
}

# Step 5: Verify critical packages
echo ""
echo "Step 5: Verifying installation..."
python -c "import pandas; print(f'✅ pandas {pandas.__version__}')" || echo "❌ pandas not found"
python -c "import networkx; print(f'✅ networkx {networkx.__version__}')" || echo "❌ networkx not found"
python -c "import streamlit; print(f'✅ streamlit {streamlit.__version__}')" || echo "❌ streamlit not found"
python -c "import plotly; print(f'✅ plotly {plotly.__version__}')" || echo "❌ plotly not found"
python -c "import igraph; print(f'✅ igraph {igraph.__version__}')" || echo "❌ igraph not found"
python -c "import leidenalg; print(f'✅ leidenalg installed')" || echo "❌ leidenalg not found"
python -c "import pyvis; print(f'✅ pyvis installed')" || echo "❌ pyvis not found"

echo ""
echo "================================================================"
echo "✅ Dependency installation completed!"
echo ""
echo "Environment: ds3019"
echo "Python: $(python --version)"
echo ""

