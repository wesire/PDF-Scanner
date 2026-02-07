#!/bin/bash

# Quick start script for PDF Context Narrator

set -e

echo "🚀 PDF Context Narrator Quick Start"
echo "===================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. Edit it to customize your settings."
fi

# Display help
echo ""
echo "✅ Setup complete!"
echo ""
echo "You can now run the CLI:"
echo ""
echo "  PYTHONPATH=src:$PYTHONPATH python -m pdf_context_narrator --help"
echo ""
echo "Or install in development mode:"
echo ""
echo "  pip install -e ."
echo "  pdf-context-narrator --help"
echo ""
echo "Example commands:"
echo "  PYTHONPATH=src:$PYTHONPATH python -m pdf_context_narrator ingest ./pdfs/"
echo "  PYTHONPATH=src:$PYTHONPATH python -m pdf_context_narrator search 'query'"
echo "  PYTHONPATH=src:$PYTHONPATH python -m pdf_context_narrator summarize doc.pdf"
echo ""
