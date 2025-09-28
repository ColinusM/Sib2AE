#!/bin/bash
# Sib2Ae GUI Launcher
# Simple script to launch the Sib2Ae pipeline GUI

echo "🎵 Starting Sib2Ae Pipeline GUI..."
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Launch the GUI (now in same directory)
python3 sib2ae_gui.py

echo "GUI closed."