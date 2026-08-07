"""
update_catalog.py — merge one survey_device.py result into
dumps/control_catalog.json (repo root) and update the coverage summary.

Pure stdlib JSON bookkeeping; run under any python. Read-only with respect to
Ableton. Re-runnable: merging the same device slug twice overwrites that
context rather than duplicating it.

Usage:
    python update_catalog.py <device_json> [--device-name <name>]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "dumps" / "control_catalog.json"


def load_catalog() -> dict:
    if CATALOG.exists():
        with open(CATALOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "generated": None,
        "environment": "Ableton Live 12 Suite, WSL2 + Windows Python",
        "coverage_summary": {
            "contexts_attempted": 0,
            "mapped": 0,
            "unmapped": 0,
            "opaque": 0,
            "load_failed": 0,
            "controls_total": 0,
            "run_time_seconds": 0,
            "load_tier_usage": {"mcp": 0, "uia_browser": 0, "failed": 0},
            "unexpected_errors": [],
        },
        "contexts": {},
    }


def status_for(result: dict) -> tuple[str, str]:
    """Return (status, note). Status from survey_plan.md §9.

    "Real" controls are nodes whose automation_id is neither the device group
    itself nor a TitleBar scaffold (title text, expand button) — those always
    carry ids and would otherwise make every device look MAPPED.
    """
    if "error" in result:
        return "LOAD_FAILED", result["error"]
    controls = result.get("controls", [])
    dev_aid = result.get("device_aid")
    real_with_aid = [
        c for c in controls
        if c.get("automation_id")
        and c.get("automation_id") != dev_aid
        and ".TitleBar." not in (c.get("automation_id") or "")
    ]
    if result.get("view_state") == "opaque" or not controls or result.get("node_count", 0) <= 1:
        return "OPAQUE", f"no child controls exposed; nodes={result.get('node_count')}"
    if not real_with_aid:
        return "UNMAPPED", "controls rendered but none carry a usable automation_id"
    return "MAPPED", ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device_json", type=str)
    parser.add_argument("--device-name", type=str, default=None)
    parser.add_argument("--category", type=str, default="audio_effects")
    parser.add_argument("--tier", type=str, default="mcp")
    parser.add_argument("--class-name", type=str, default="")
    parser.add_argument("--note", type=str, default="")
    args = parser.parse_args()

    with open(args.device_json, "r", encoding="utf-8") as f:
        result = json.load(f)

    name = args.device_name or result.get("device_name", Path(args.device_json).stem)
    status, note = status_for(result)

    cat = load_catalog()

    context = {
        "status": status,
        "category": args.category,
        "loaded_via": args.tier,
        "device_class": args.class_name,
        "view_state": result.get("view_state"),
        "node_count": result.get("node_count"),
        "controls_with_automation_id": result.get("controls_with_automation_id"),
        "title_matched": result.get("title_matched"),
        "expand_clicked": result.get("expand_clicked"),
        "notes": (note or args.note).strip(),
        "controls": [],
    }

    for c in result.get("controls", []):
        patterns = c.get("patterns", {})
        context["controls"].append({
            "name": c.get("name", ""),
            "automation_id": c.get("automation_id") or None,
            "control_type": c.get("control_type"),
            "value_pattern_available": bool(patterns),
            "patterns": patterns,
            "bounding_rect": c.get("bounding_rect", {}),
        })

    cat["contexts"][name] = context

    # Recompute coverage summary from actual contexts (source of truth).
    ctxs = cat["contexts"]
    counts = {"MAPPED": 0, "UNMAPPED": 0, "OPAQUE": 0, "LOAD_FAILED": 0}
    total_controls = 0
    for ctx in ctxs.values():
        counts[ctx.get("status", "LOAD_FAILED")] += 1
        total_controls += len(ctx.get("controls", []))
    s = cat["coverage_summary"]
    s["contexts_attempted"] = len(ctxs)
    s["mapped"] = counts["MAPPED"]
    s["unmapped"] = counts["UNMAPPED"]
    s["opaque"] = counts["OPAQUE"]
    s["load_failed"] = counts["LOAD_FAILED"]
    s["controls_total"] = total_controls

    cat["generated"] = datetime.now(timezone.utc).isoformat()
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2, ensure_ascii=False)

    print(f"[{status}] {name}: {len(context['controls'])} controls, "
          f"{result.get('controls_with_automation_id')} with automation_id, "
          f"view_state={result.get('view_state')}")
    print(f"catalog -> {CATALOG} (contexts={s['contexts_attempted']}, "
          f"controls={s['controls_total']}, M={s['mapped']} U={s['unmapped']} "
          f"O={s['opaque']} LF={s['load_failed']})")


if __name__ == "__main__":
    main()
