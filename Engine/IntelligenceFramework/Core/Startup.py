"""
======================================================================
ENGINE INTELLIGENCE FRAMEWORK
STARTUP
======================================================================
"""

import sys
from pathlib import Path

# ----------------------------------------------------------
# Configure Python search path FIRST
# ----------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ----------------------------------------------------------
# Framework Imports
# ----------------------------------------------------------

from Engine.IntelligenceFramework.Core.Bootstrap import bootstrap
from Engine.IntelligenceFramework.Core.FrameworkManager import FrameworkManager

# ----------------------------------------------------------
# Startup
# ----------------------------------------------------------

def main():

    bootstrap()

    manager = FrameworkManager()
    manager.boot()


if __name__ == "__main__":
    main()
