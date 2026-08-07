"""
browser_switch.py — read-only survey navigation: click a Browser sidebar
category tab (Sounds / Drums / Instruments / Audio Effects / MIDI Effects /
Plug-Ins) so its item list renders, then exit.

These tabs carry empty automation_ids (survey_plan.md §5.4), so they are
matched by exact (control_type, name) on the DataItem node. No other
interaction; used only to prepare a state before survey_section.py.

Usage:
    python browser_switch.py "<Category Name>"
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_ableton_pywinauto import find_ableton_window, ensure_window_ready  # noqa: E402
from survey_device import _name, _children, _ctype  # noqa: E402


def find_dataitem(ctrl, name: str, depth: int = 0):
    if depth > 20:
        return None
    try:
        if _ctype(ctrl) == "DataItem" and _name(ctrl) == name:
            return ctrl
    except Exception:
        pass
    for c in _children(ctrl):
        r = find_dataitem(c, name, depth + 1)
        if r is not None:
            return r
    return None


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python browser_switch.py '<Category Name>'", file=sys.stderr)
        sys.exit(1)
    name = sys.argv[1]
    window = find_ableton_window()
    if window is None:
        print("Could not find the Ableton Live window.", file=sys.stderr)
        sys.exit(1)
    ensure_window_ready(window, maximize=True)
    tab = find_dataitem(window, name)
    if tab is None:
        print(f"Browser category DataItem {name!r} not found.", file=sys.stderr)
        sys.exit(1)
    tab.click_input()
    time.sleep(0.6)
    print(f"Clicked Browser category {name!r}.")


if __name__ == "__main__":
    main()
