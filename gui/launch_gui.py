#!/usr/bin/env python3
"""
GUI Launcher - Launch the Sib2Ae GUI from the gui module
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and launch GUI
from gui.sib2ae_gui import main

if __name__ == "__main__":
    main()