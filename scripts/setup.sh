#!/bin/bash
set -e

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .
pip install -e ".[dev]"

# Create necessary directories
echo "Creating output directory..."
mkdir -p output

echo "Setup complete! Activate the virtual environment with 'source venv/bin/activate'"
