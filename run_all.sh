#!/bin/bash
# Complete Run Script for Conda Environment
# Runs the entire pipeline from data cleaning to web app

set -e

echo "🚀 Starting Citation Network Analysis Pipeline"
echo "=============================================="
echo "Using conda environment: ds3019"
echo ""

# Initialize conda
eval "$(conda shell.bash hook)"

# Activate conda environment
echo "Activating conda environment: ds3019..."
conda activate ds3019

# Change to project directory
cd "$(dirname "$0")"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "💡 Create a .env file with your API keys (see .env.example)"
    echo ""
fi

# Step 1: Data Cleaning
echo ""
echo "Step 1: Data Cleaning..."
if [ -f "2data_processor.py" ]; then
    python 2data_processor.py
    if [ $? -eq 0 ]; then
        echo "✅ Data cleaning completed"
    else
        echo "❌ Data cleaning failed"
        exit 1
    fi
else
    echo "⚠️  2data_processor.py not found, skipping..."
fi
echo ""

# Step 2: PageRank Analysis
echo "Step 2: PageRank Analysis..."
if [ -f "pagerank_analyzer.py" ]; then
    python pagerank_analyzer.py
    if [ $? -eq 0 ]; then
        echo "✅ PageRank analysis completed"
    else
        echo "❌ PageRank analysis failed"
        exit 1
    fi
else
    echo "⚠️  pagerank_analyzer.py not found, skipping..."
fi
echo ""

# Step 3: Visualization
echo "Step 3: Generating Visualizations..."
if [ -f "3visual.py" ]; then
    python 3visual.py
    if [ $? -eq 0 ]; then
        echo "✅ Visualization generation completed"
    else
        echo "❌ Visualization generation failed"
        exit 1
    fi
else
    echo "⚠️  3visual.py not found, skipping..."
fi
echo ""

# Step 4: Check if all required files exist
echo "Step 4: Checking required files..."
required_files=("papers_cleaned.csv" "edges_cleaned.csv" "node_leiden_comm.csv")
missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file not found"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo ""
    echo "✅ All required files are present!"
    echo ""
    echo "Step 5: Starting Web Application..."
    echo "=============================================="
    echo "📱 Web app will be available at: http://localhost:8501"
    echo "🛑 Press Ctrl+C to stop the server"
    echo ""
    streamlit run 4app.py
else
    echo ""
    echo "⚠️  Some required files are missing. Please run the previous steps first."
    echo "Missing files: ${missing_files[*]}"
    exit 1
fi

