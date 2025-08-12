#!/bin/bash
# Financial Analysis System - Installation Script
# 财务分析系统 - 安装脚本

echo "=========================================="
echo "Financial Analysis System v3.2 Installation"
echo "=========================================="

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $python_version"

# Install core dependencies with specific versions
echo ""
echo "Installing core dependencies..."
pip install --upgrade pip --quiet
pip install numpy==1.24.3 --quiet
pip install pandas==1.5.3 --quiet
pip install -r requirements.txt --quiet

# OCR support (optional)
echo ""
echo "Checking OCR support..."
if command -v tesseract &> /dev/null; then
    echo "✓ Tesseract is installed"
else
    echo "✗ Tesseract not found"
    echo "  To install on macOS: brew install tesseract tesseract-lang"
    echo "  To install on Linux: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim"
fi

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Quick start:"
echo "  python main.py download --limit 10   # Download reports"
echo "  python main.py extract --limit 10    # Extract data"
echo "  python main.py analyze                # Analyze results"
echo ""