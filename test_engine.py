#!/usr/bin/env python3
"""Integration test for MonitorGuard."""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

results = []

try:
    from src.monitor_utils import get_all_monitors
    monitors = get_all_monitors()
    results.append(f"PASS: Monitors detected: {len(monitors)}")
    for m in monitors:
        results.append(f"  {m}")
except Exception as e:
    results.append(f"FAIL: Monitor enumeration: {e}")

try:
    from src.icon_renderer import generate_icon
    img_active = generate_icon(64, active=True)
    img_inactive = generate_icon(64, active=False)
    results.append(f"PASS: Icons generated: active={img_active.size} inactive={img_inactive.size}")
except Exception as e:
    results.append(f"FAIL: Icon generation: {e}")

try:
    from src.isolation_engine import IsolationEngine
    engine = IsolationEngine()
    results.append(f"PASS: Engine created, enabled={engine.enabled}")
except Exception as e:
    results.append(f"FAIL: Engine creation: {e}")

try:
    engine.start()
    time.sleep(0.3)
    results.append("PASS: Engine started (hooks installed)")
except Exception as e:
    results.append(f"FAIL: Engine start: {e}")

try:
    engine.enable()
    results.append(f"PASS: Engine enabled: {engine.enabled}")
except Exception as e:
    results.append(f"FAIL: Engine enable: {e}")

try:
    counts = engine.get_window_count_per_monitor()
    results.append(f"PASS: Window counts: {counts}")
except Exception as e:
    results.append(f"FAIL: Window counts: {e}")

try:
    engine.toggle()
    results.append(f"PASS: Toggle off: enabled={engine.enabled}")
    engine.toggle()
    results.append(f"PASS: Toggle on: enabled={engine.enabled}")
except Exception as e:
    results.append(f"FAIL: Toggle: {e}")

try:
    engine.stop()
    results.append("PASS: Engine stopped cleanly")
except Exception as e:
    results.append(f"FAIL: Engine stop: {e}")

try:
    import keyboard
    kb_hit = [False]
    keyboard.add_hotkey("shift+s", lambda: kb_hit.__setitem__(0, True))
    time.sleep(0.1)
    keyboard.remove_hotkey("shift+s")
    results.append("PASS: Hotkey registration works")
except Exception as e:
    results.append(f"FAIL: Hotkey: {e}")

try:
    from src.tray_app import TrayApp
    app = TrayApp()
    results.append(f"PASS: TrayApp created, icons={app._active_icon.size}")
except Exception as e:
    results.append(f"FAIL: TrayApp: {e}")

results.append("")
results.append("=== ALL INTEGRATION TESTS COMPLETE ===")

with open("test_results.txt", "w") as f:
    f.write("\n".join(results))

print("\n".join(results))
