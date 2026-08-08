"""
survey_value_patterns.py

Phase C survey tool: probe UI Automation value patterns on Ableton Live
controls. Read-only -- does not click, type, or otherwise control Live.

For every element in the Ableton window tree that carries a real
`automation_id`, this checks whether the element exposes a
`RangeValuePattern` and/or `ValuePattern` via pywinauto's
`iface_range_value` / `iface_value` lazy properties (both raise
`NoPatternInterfaceError` when the pattern is absent).

Per AGENTS.md Phase C the expected finding is that sliders/knobs are
LARGELY ABSENT of RangeValuePattern (Ableton renders them custom); the
exceptions are the useful ones and are surfaced as
`value_pattern_controls` counts below.

Output
------
Merges two top-level fields into the target device JSON (given by
--json), leaving the original tree untouched:

    value_pattern_available: bool
        True if any probed control exposed RangeValuePattern or
        ValuePattern, else False.

    value_pattern_stats: {
        "controls_probed": int,
        "range_value": int,        # controls exposing RangeValuePattern
        "value_pattern": int,      # controls exposing ValuePattern
        "by_control_type": { control_type: {"probed": n,
                                            "range_value": n,
                                            "value_pattern": n} },
        "range_value_examples": [ {control_type, name, automation_id,
                                   min, max, value} ... ],
        "value_examples":      [ {control_type, name, automation_id,
                                   value} ... ]
    }

Usage
-----
    python survey_value_patterns.py --json dumps/device_EQ-Eight.json
    python survey_value_patterns.py --json dumps/device_EQ-Eight.json --no-print
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from dump_ableton_pywinauto import (
    find_ableton_window,
    ensure_window_ready,
    WINDOW_TITLE_SUBSTRING,
)

try:
    from pywinauto import Desktop
    from pywinauto.controls.uiawrapper import UIAWrapper
except ImportError:
    print(
        "Missing dependency. Install with: pip install pywinauto",
        file=sys.stderr,
    )
    sys.exit(1)

from pywinauto.uia_defines import NoPatternInterfaceError


def _probe(wrapper: UIAWrapper) -> tuple[bool, bool, dict, dict]:
    """Return (has_range_value, has_value_pattern, range_info, value_info)."""
    range_info, value_info = {}, {}

    try:
        rv = wrapper.iface_range_value
        has_range = True
        try:
            range_info = {
                "min": float(rv.CurrentMinimum),
                "max": float(rv.CurrentMaximum),
                "value": float(rv.CurrentValue),
            }
        except Exception:
            range_info = {}
    except NoPatternInterfaceError:
        has_range = False
    except Exception:
        has_range = False

    try:
        vp = wrapper.iface_value
        has_value = True
        try:
            value_info = {
                "value": str(vp.CurrentValue),
                "read_only": bool(vp.IsReadOnly),
            }
        except Exception:
            value_info = {}
    except NoPatternInterfaceError:
        has_value = False
    except Exception:
        has_value = False

    return has_range, has_value, range_info, value_info


def walk_probe(
    control: UIAWrapper, stats: dict, examples: dict, max_depth: int, depth: int = 0
) -> None:
    try:
        control_type = control.element_info.control_type or ""
    except Exception:
        control_type = ""
    try:
        name = (control.window_text() or "").strip()
    except Exception:
        name = ""
    try:
        automation_id = control.element_info.automation_id or ""
    except Exception:
        automation_id = ""

    has_range, has_value, rinfo, vinfo = _probe(control)

    if automation_id.strip():
        stats["controls_probed"] += 1
        ct = control_type or "(none)"
        bucket = stats["by_control_type"].setdefault(
            ct, {"probed": 0, "range_value": 0, "value_pattern": 0}
        )
        bucket["probed"] += 1
        if has_range:
            bucket["range_value"] += 1
            stats["range_value"] += 1
            if len(examples["range_value"]) < 50:
                examples["range_value"].append(
                    {
                        "control_type": ct,
                        "name": name,
                        "automation_id": automation_id,
                        **rinfo,
                    }
                )
        if has_value:
            bucket["value_pattern"] += 1
            stats["value_pattern"] += 1
            if len(examples["value_pattern"]) < 50:
                examples["value_pattern"].append(
                    {
                        "control_type": ct,
                        "name": name,
                        "automation_id": automation_id,
                        **vinfo,
                    }
                )

    if depth >= max_depth:
        return

    try:
        children = control.children()
    except Exception:
        children = []
    for child in children:
        walk_probe(child, stats, examples, max_depth, depth + 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        type=str,
        required=True,
        help="Path to the existing device_<Name>.json dump; the "
        "value-pattern fields are merged into this file.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="How many levels deep to recurse (default: 10).",
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Skip stdout summary (avoids cp1252 console crashes).",
    )
    parser.add_argument(
        "--title-contains",
        type=str,
        default=WINDOW_TITLE_SUBSTRING,
        help="Window title substring to match.",
    )
    args = parser.parse_args()

    print("Looking for the Ableton Live window...", file=sys.stderr)
    window = find_ableton_window(title_contains=args.title_contains)
    if window is None:
        print("Could not find the Ableton Live window.", file=sys.stderr)
        sys.exit(1)

    ensure_window_ready(window, maximize=True)

    stats = {
        "controls_probed": 0,
        "range_value": 0,
        "value_pattern": 0,
        "by_control_type": {},
    }
    examples = {"range_value": [], "value_pattern": []}

    walk_probe(window, stats, examples, max_depth=args.max_depth)

    value_pattern_available = (
        stats["range_value"] > 0 or stats["value_pattern"] > 0
    )

    with open(args.json, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["value_pattern_available"] = value_pattern_available
    data["value_pattern_stats"] = {
        "controls_probed": stats["controls_probed"],
        "range_value": stats["range_value"],
        "value_pattern": stats["value_pattern"],
        "by_control_type": stats["by_control_type"],
        "range_value_examples": examples["range_value"],
        "value_examples": examples["value_pattern"],
    }

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    if not args.no_print:
        print(
            f"\nvalue_pattern_available: {value_pattern_available} "
            f"(probed {stats['controls_probed']}, "
            f"range_value {stats['range_value']}, "
            f"value_pattern {stats['value_pattern']})"
        )
    print(
        f"Updated {args.json} with value-pattern fields.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
