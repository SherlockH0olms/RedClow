#!/usr/bin/env python3
"""
RedClaw - Autonomous Red Team AI Agent
Main entry point
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from redclaw.cli.main import main

if __name__ == "__main__":
    main()
