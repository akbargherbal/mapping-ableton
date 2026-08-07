"""
survey_section.py — read-only UIA survey helper for a named UI section
(context), e.g. the Arrangement View, Browser panel, a track/return/master
mixer strip, or Clip Detail.

Read-only (AGENTS.md §9): walks the live tree and queries UIA patterns only;
no clicking, no MCP, no action/task code. Reuses the walk/probe helpers from
survey_device.py.

Usage:
    python survey_section.py "<Context Key>" --aid <automation_id_prefix>
    python survey_section.py "<Context Key>" --name <exact group name>
    python survey_section.py "<Context Key>" --name <name> --instance <n>   # nth match

Finds the FIRST group whose automation_id starts with --aid (or whose name
equals --name, optionally the nth match), walks its subtree, and writes a JSON
result to <scripts>/dumps/section_<slug>.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_ableton_pywinauto import find_ableton_window, ensure_window_ready  # noqa: E402
from survey_device import _aid, _ctype, _name, _rect, _children, probe_patterns  # noqa: E402


def find_by_aid_prefix(ctrl, prefix: str, depth: int = 0) -> Optional[object]:
    if depth > 24:
        return None
    a = _aid(ctrl) or ""
    if a == prefix or a.startswith(prefix):
        return ctrl
    for c in _children(ctrl):
        r = find_by_aid_prefix(c, prefix, depth + 1)
        if r is not None:
            return r
    return None


def find_by_name(ctrl, name: str, instance: int = 0, depth: int = 0,
                 _seen: Optional[list] = None) -> Optional[object]:
    if _seen is None:
        _seen = []
    if depth > 24:
        return None
    if _name(ctrl) == name:
        _seen.append(ctrl)
        if len(_seen) == instance + 1:
            return ctrl
    for c in _children(ctrl):
        r = find_by_name(c, name, instance, depth + 1, _seen)
        if r is not None:
            return r
    return None


def walk_controls(dev, depth: int = 0) -> list:
    if depth > 14:
        return []
    nodes = [{
        "control_type": _ctype(dev),
        "name": _name(dev),
        "automation_id": _aid(dev),
        "bounding_rect": _rect(dev),
        "patterns": probe_patterns(dev),
    }]
    for c in _children(dev):
        nodes.extend(walk_controls(c, depth + 1))
    return nodes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context_key", type=str)
    parser.add_argument("--aid", type=str, default=None)
    parser.add_argument("--name", type=str, default=None)
    parser.add_argument("--instance", type=int, default=0)
    parser.add_argument("--slug", type=str, default=None)
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    if not args.aid and not args.name:
        parser.error("provide --aid or --name")

    window = find_ableton_window()
    if window is None:
        print("Could not find the Ableton Live window.", file=sys.stderr)
        sys.exit(1)
    ensure_window_ready(window, maximize=True)

    if args.aid:
        sec = find_by_aid_prefix(window, args.aid)
        how = f"aid prefix {args.aid!r}"
    else:
        sec = find_by_name(window, args.name, args.instance)
        how = f"name {args.name!r} instance {args.instance}"

    if sec is None:
        print(f"Section not found ({how}).", file=sys.stderr)
        sys.exit(1)

    slug = args.slug or "".join(
        c if (c.isalnum() or c in "-_") else "-" for c in args.context_key
    ).strip("-")
    out_dir = Path(args.out).resolve() if args.out else Path(__file__).resolve().parent / "dumps"
    out_dir.mkdir(parents=True, exist_ok=True)

    controls = walk_controls(sec)
    with_aid = [c for c in controls if c.get("automation_id")]
    result = {
        "context_key": args.context_key,
        "section_aid": _aid(sec),
        "section_name": _name(sec),
        "found_by": how,
        "node_count": len(controls),
        "controls_with_automation_id": len(with_aid),
        "controls": controls,
    }
    path = out_dir / f"section_{slug}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Wrote {path}", file=sys.stderr)
    print(f"  {args.context_key}: nodes={result['node_count']} "
          f"with_aid={result['controls_with_automation_id']}")


if __name__ == "__main__":
    main()
