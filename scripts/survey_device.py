"""
survey_device.py — read-only UIA survey helper for one loaded Ableton device.

Surveys the device currently rendered under `TrackView.Device[i]` in the Device
Detail panel whose title-bar text matches the device name given on the command
line. Records every control in that device's subtree (control_type, name,
automation_id, bounding_rect) plus, for each control, which UIA value patterns
are live (RangeValue / Toggle / Selection) and their current values.

Read-only by design (AGENTS.md §9): walks the live tree and queries UIA patterns
only. The ONE interaction is the expand step from survey_plan.md §5 policy — a
single click on a title-bar checkbox named exactly "Toggle Expanded View" when it
is present and unchecked. No other clicking; no MCP; no action/task code.

Imports only from dump_ableton_pywinauto.py (imports cleanly; the modules that
import the missing keyboard_shortcuts.py are deliberately not used).

Usage:
    python survey_device.py "<Device Name>" [--slug <slug>] [--out <path>]

Output:
    JSON with device name, view-state facts (node counts, expand flags,
    ViewMode presence), and the control list. Default written to
    <scripts>/dumps/device_<slug>.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_ableton_pywinauto import find_ableton_window, ensure_window_ready  # noqa: E402


def _aid(ctrl) -> Optional[str]:
    try:
        return ctrl.element_info.automation_id
    except Exception:
        return None


def _ctype(ctrl) -> Optional[str]:
    try:
        return ctrl.element_info.control_type
    except Exception:
        return None


def _name(ctrl) -> str:
    try:
        return (ctrl.window_text() or "").strip()
    except Exception:
        return ""


def _rect(ctrl) -> dict:
    try:
        r = ctrl.rectangle()
        return {"left": r.left, "top": r.top, "right": r.right, "bottom": r.bottom}
    except Exception:
        return {}


def _children(ctrl) -> list:
    try:
        return ctrl.children() or []
    except Exception:
        return []


def find_aid(ctrl, target_aid: str, depth: int = 0) -> Optional[object]:
    """DFS for the first descendant with automation_id == target_aid."""
    if depth > 20:
        return None
    if _aid(ctrl) == target_aid:
        return ctrl
    for c in _children(ctrl):
        r = find_aid(c, target_aid, depth + 1)
        if r is not None:
            return r
    return None


def find_device_groups(window) -> list:
    """All TrackView.Device[i] groups currently rendered."""
    root = find_aid(window, "TrackView")
    if root is None:
        return []
    groups = []
    for c in _children(root):
        aid = _aid(c)
        if aid and aid.startswith("TrackView.Device["):
            groups.append(c)
    return groups


def device_title(dev) -> str:
    t = find_aid(dev, f"{_aid(dev)}.TitleBar.device_title")
    return _name(t) if t is not None else ""


def probe_patterns(ctrl) -> dict:
    """Which UIA patterns are live on this control, with current values."""
    out = {}
    try:
        out["range_value"] = round(float(ctrl.get_range_value()), 4)
    except Exception:
        pass
    try:
        out["toggle_state"] = bool(ctrl.get_toggle_state())
    except Exception:
        pass
    try:
        out["selection"] = bool(ctrl.get_selection_indicator())
    except Exception:
        pass
    try:
        out["value"] = ctrl.get_value()
    except Exception:
        pass
    return out


def walk_controls(dev, depth: int = 0) -> list:
    """Collect every control in a device subtree (breadth includes the device
    group itself so an OPAQUE device still yields one node)."""
    if depth > 12:
        return []
    nodes = []
    ctype = _ctype(dev)
    aid = _aid(dev)
    nodes.append({
        "control_type": ctype,
        "name": _name(dev),
        "automation_id": aid,
        "bounding_rect": _rect(dev),
        "patterns": probe_patterns(dev),
    })
    for c in _children(dev):
        nodes.extend(walk_controls(c, depth + 1))
    return nodes


def collect(window, device_name: str, slug: str) -> dict:
    ensure_window_ready(window, maximize=True)

    groups = find_device_groups(window)
    if not groups:
        return {
            "device_name": device_name,
            "error": "no TrackView.Device groups rendered (track not selected? "
                     "device not visible?)",
            "view_state": "absent",
        }

    # Prefer the device whose title matches; else fall back to the last group.
    dev = None
    matched = False
    for g in groups:
        if device_title(g).strip().lower() == device_name.strip().lower():
            dev, matched = g, True
            break
    if dev is None:
        dev = groups[-1]
        matched = False

    dev_aid = _aid(dev)
    title = device_title(dev)

    # Expand step (survey_plan.md §5): only the checkbox named exactly
    # "Toggle Expanded View", present and unchecked.
    expand_clicked = False
    eb = find_aid(dev, f"{dev_aid}.TitleBar.ExtendViewButton")
    if eb is not None and _name(eb) == "Toggle Expanded View":
        try:
            st = bool(eb.get_toggle_state())
        except Exception:
            st = None
        if st is False:
            try:
                eb.click_input()
                time.sleep(0.6)
                expand_clicked = True
            except Exception:
                pass

    controls = walk_controls(dev)
    with_aid = [c for c in controls if c.get("automation_id")]
    total_nodes = len(controls)
    has_viewmode = any("ViewMode" in (c.get("automation_id") or "") for c in controls)
    has_children = any(True for c in _children(dev))

    if not has_children:
        view_state = "opaque"
    elif has_viewmode:
        view_state = "compact"
    else:
        view_state = "expanded"

    return {
        "device_name": device_name,
        "slug": slug,
        "device_aid": dev_aid,
        "title_found": title,
        "title_matched": matched,
        "view_state": view_state,
        "node_count": total_nodes,
        "controls_with_automation_id": len(with_aid),
        "expand_button_present": eb is not None,
        "expand_clicked": expand_clicked,
        "has_viewmode_radios": has_viewmode,
        "controls": controls,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device_name", type=str)
    parser.add_argument("--slug", type=str, default=None)
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    slug = args.slug or "".join(
        c if (c.isalnum() or c in "-_") else "-" for c in args.device_name
    ).strip("-")
    out_dir = Path(args.out).resolve() if args.out else Path(__file__).resolve().parent / "dumps"
    out_dir.mkdir(parents=True, exist_ok=True)

    window = find_ableton_window()
    if window is None:
        print("Could not find the Ableton Live window.", file=sys.stderr)
        sys.exit(1)

    result = collect(window, args.device_name, slug)
    path = out_dir / f"device_{slug}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Wrote {path}", file=sys.stderr)
    print(
        f"  {args.device_name}: view_state={result.get('view_state')} "
        f"nodes={result.get('node_count')} "
        f"with_aid={result.get('controls_with_automation_id')} "
        f"title_matched={result.get('title_matched')}"
    )


if __name__ == "__main__":
    main()
