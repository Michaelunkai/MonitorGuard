#!/usr/bin/env python3
"""
MonitorGuard — Multi-Monitor Isolation for Windows
===================================================

System tray application that creates complete isolation boundaries between
every connected monitor. As long as it's running:

  • Each monitor is a sealed environment — nothing crosses the boundary.
  • A beautiful shield icon in the system tray shows live status.
  • Press Shift+S to toggle isolation on/off.
  • No port/pipe/resource conflicts with other processes.
  • Zero performance impact on games or GPU-heavy apps.

Usage:
    python main.py          Launch with isolation ON by default
    python main.py --off    Launch with isolation OFF (standalone)
    python main.py --debug  Launch with debug logging
"""

import sys
import os
import logging
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="MonitorGuard — Multi-Monitor Isolation")
    parser.add_argument("--off", action="store_true", help="Start with isolation disabled")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(debug=args.debug)
    log = logging.getLogger("MonitorGuard.main")

    # Verify Windows
    if sys.platform != "win32":
        log.error("MonitorGuard requires Windows. Detected platform: %s", sys.platform)
        sys.exit(1)

    # Check for multiple monitors
    from src.monitor_utils import get_all_monitors
    monitors = get_all_monitors()
    log.info(f"Detected {len(monitors)} monitor(s)")
    for m in monitors:
        log.info(f"  {m}")

    if len(monitors) < 1:
        log.warning("No monitors detected — isolation will have no effect")

    # Start the tray app
    from src.tray_app import TrayApp
    app = TrayApp()

    if args.off:
        log.info("Starting with isolation OFF (use Shift+S to enable)")
    else:
        log.info("Starting with isolation ON (use Shift+S to toggle)")
        app.engine.enable()

    try:
        app.run()
    except Exception as e:
        log.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
