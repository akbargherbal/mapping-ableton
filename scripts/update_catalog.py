"""
update_catalog.py

Merge the per-context survey dumps in scripts/dumps/ into a single
control_catalog.json (AGENTS.md section 8).

The survey's raw output is the set of per-context files produced by the
phase scripts:

  device_<Name>.json                       -- Phase A/B device dumps
  section_<Name>.json                      -- Phase D/F/G extracted views
  ableton_uia_*_<category>.json            -- Phase E browser categories
                                              (timestamped names)

This script reads every dump it can identify, flattens each one's UIA
tree into a per-context entry, and writes one JSON document grouped by
context. It is intentionally read-only over the dumps and never talks to
Ableton; it only records automation_ids actually present in the dumps
(NEVER inferred -- AGENTS.md section 10).

Per-context status semantics (AGENTS.md section 8):

  MAPPED      one or more controls carry a real, stable automation_id
  UNMAPPED    controls present but no usable automation_id was observed
  OPAQUE      panel confirmed rendered but exposes no children at all
              (the section file itself marks "status": "OPAQUE")
  LOAD_FAILED a phase recorded the device/context as unplaceable
              (propagated from a "status": "LOAD_FAILED" marker)

The value-pattern fields written by survey_value_patterns.py (Phase C)
are carried through on the relevant device contexts.

Output: dumps/control_catalog.json  (relative to --dumps-dir)

Usage (from inside scripts/):
    python update_catalog.py
    python update_catalog.py --dumps-dir dumps
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import OrderedDict
from datetime import datetime, timezone


def _walk(node, path):
    yield path, node
    for child in node.get("children") or []:
        yield from _walk(child, path + [child.get("name", "")])


def _flatten_context(filepath, root):
    """Return a dict with the control inventory for one dump file.

    Controls = leaf-ish nodes. We record:
      - mapped:   {automation_id, control_type, name, path}
      - unmapped: {control_type, name, path} for named nodes without id
                  (capped to avoid unbounded growth on 1001-item lists)
    """
    mapped, unmapped = [], []
    max_unmapped = 2000

    for path, node in _walk(root, [root.get("name", "")]):
        aid = node.get("automation_id") or ""
        ct = node.get("control_type") or ""
        name = node.get("name") or ""
        has_children = bool(node.get("children"))

        if aid.strip():
            mapped.append(
                {
                    "automation_id": aid,
                    "control_type": ct,
                    "name": name,
                    "path": "/".join(p for p in path if p),
                }
            )
        elif name.strip() and not has_children and len(unmapped) < max_unmapped:
            unmapped.append(
                {
                    "control_type": ct,
                    "name": name,
                    "path": "/".join(p for p in path if p),
                }
            )

    # de-duplicate mapped by automation_id (keep first occurrence)
    seen = set()
    unique_mapped = []
    for c in mapped:
        if c["automation_id"] in seen:
            continue
        seen.add(c["automation_id"])
        unique_mapped.append(c)

    return {
        "mapped": unique_mapped,
        "unmapped": unmapped,
        "mapped_count": len(unique_mapped),
        "unmapped_count": len(unmapped),
    }


_CONTEXT_STATUS_OVERRIDE = ("status",)


def _context_from_device(filename):
    m = re.match(r"^device_(.+)\.json$", filename)
    return f"device:{m.group(1)}" if m else None


def _context_from_section(filename):
    m = re.match(r"^section_(.+)\.json$", filename)
    return f"section:{m.group(1)}" if m else None


def _context_from_browser(filename):
    m = re.match(r"^ableton_uia_\d+_\d+_(.+)\.json$", filename)
    return f"browser:{m.group(1)}" if m else None


def _identify_context(filename):
    for fn in (
        _context_from_device,
        _context_from_section,
        _context_from_browser,
    ):
        ctx = fn(filename)
        if ctx:
            return ctx
    return None


def _status_for(context_key, inventory, root_meta):
    # OPAQUE / LOAD_FAILED markers written by the phase scripts win.
    if root_meta.get("status"):
        return root_meta["status"]
    if inventory["mapped_count"] > 0:
        return "MAPPED"
    if inventory["unmapped_count"] > 0:
        return "UNMAPPED"
    return "OPAQUE"


def build_catalog(dumps_dir):
    catalog = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "survey_complete": True,
        "phases_covered": ["A", "B", "C", "D", "E", "F", "G"],
        "contexts": OrderedDict(),
        "summary": {},
    }

    patterns = [
        "device_*.json",
        "section_*.json",
        "ableton_uia_*_*.json",
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(dumps_dir, pat)))

    browser_by_cat = {}
    for f in sorted(set(files)):
        filename = os.path.basename(f)
        ctx = _identify_context(filename)
        if ctx is None:
            continue

        if ctx.startswith("browser:"):
            # keep only the most recent dump per browser category
            stamp = re.match(r"^ableton_uia_(\d+_\d+)_", filename)
            key = (ctx, stamp.group(1) if stamp else "")
            browser_by_cat.setdefault(ctx, (key, f))
            if key > browser_by_cat[ctx][0]:
                browser_by_cat[ctx] = (key, f)
            continue

        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as e:
            catalog["summary"].setdefault("errors", []).append(
                {"file": filename, "error": str(e)}
            )
            continue

        inventory = _flatten_context(filename, data)
        root_meta = {k: v for k, v in data.items()
                     if k in ("status", "notes", "value_pattern_available")}
        status = _status_for(ctx, inventory, root_meta)
        entry = {
            "status": status,
            "source": filename,
            "mapped_controls": inventory["mapped"],
            "unmapped_controls": inventory["unmapped"],
            "automation_id_count": inventory["mapped_count"],
        }
        for key in ("value_pattern_available",):
            if key in root_meta:
                entry[key] = root_meta[key]
        if root_meta.get("notes"):
            entry["notes"] = root_meta["notes"]
        catalog["contexts"][ctx] = entry

    # attach the browser categories (latest per category)
    for ctx in sorted(browser_by_cat):
        _, f = browser_by_cat[ctx]
        filename = os.path.basename(f)
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as e:
            catalog["summary"].setdefault("errors", []).append(
                {"file": filename, "error": str(e)}
            )
            continue
        inventory = _flatten_context(filename, data)
        # The survey target for a browser category is its item list,
        # which carries empty automation_ids (Phase E finding). The
        # mapped controls in the dump are window chrome (MenuBar,
        # Transport, etc.) that is already covered under its own
        # context -- so the category context itself is UNMAPPED.
        status = "UNMAPPED"
        entry = {
            "status": status,
            "source": filename,
            "mapped_controls": inventory["mapped"],
            "unmapped_controls": inventory["unmapped"],
            "automation_id_count": inventory["mapped_count"],
            "notes": "Browser category item list; the items themselves "
            "carry empty automation_ids (Phase E finding). Any "
            "mapped_controls in this dump are surrounding window "
            "chrome (MenuBar, Transport, ...) also covered by other "
            "contexts.",
        }
        catalog["contexts"][ctx] = entry

    # summary counts
    by_status = {}
    for ctx, entry in catalog["contexts"].items():
        st = entry["status"]
        by_status.setdefault(st, 0)
        by_status[st] += 1
    catalog["summary"]["context_count"] = len(catalog["contexts"])
    catalog["summary"]["by_status"] = by_status
    catalog["summary"]["total_mapped_controls"] = sum(
        e["automation_id_count"] for e in catalog["contexts"].values()
    )

    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dumps-dir",
        type=str,
        default="dumps",
        help="Directory containing the per-context dump files "
        "(default: dumps, relative to CWD).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output path (default: <dumps-dir>/control_catalog.json).",
    )
    args = parser.parse_args()

    catalog = build_catalog(args.dumps_dir)
    out = args.out or os.path.join(args.dumps_dir, "control_catalog.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, indent=2, ensure_ascii=False)

    print(
        f"Wrote {out}: {catalog['summary']['context_count']} contexts "
        f"{catalog['summary']['by_status']}, "
        f"{catalog['summary']['total_mapped_controls']} mapped controls",
        file=__import__("sys").stderr,
    )


if __name__ == "__main__":
    main()
