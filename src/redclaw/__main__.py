#!/usr/bin/env python3
"""
RedClaw v2.0 - Main Entry Point
Run with: python -m redclaw
"""

import sys
import asyncio


def main():
    """Main entry point"""
    from redclaw.cli.app import RedClawApp
    
    app = RedClawApp()
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
