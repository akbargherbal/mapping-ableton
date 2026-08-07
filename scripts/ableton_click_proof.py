"""
ableton_click_proof.py

ONE concrete, verifiable proof: locate a real control in a running Ableton
Live instance using an automation_id from dumps/control_catalog.json, read
its current state, click it, read its state again, and prove the click
actually changed something in Ableton -- not just that a mouse moved.

Target control (chosen from control_catalog.json's "Auto Filter" context):
    name:          "Sidechain Toggle"
    automation_id: "TrackView.Device[0].TitleBar.ExtendViewButton"
    type:          CheckBox (has a readable toggle_state: True/False)

This toggle is safe to click repeatedly -- it only expands/collapses the
device's extended view. It does not change your audio or project.

PREREQUISITES (do this in Ableton before running the script):
    1. Load the "Auto Filter" device as the FIRST device on any track.
    2. Select that track so its Device View shows Auto Filter.
       (automation_id "TrackView.Device[0]" means "whatever's in device
       slot 0 of the currently selected track" -- it's slot-relative,
       not device-specific. See context.md's "Known, expected id reuse".)

MUST run under WINDOWS Python, not WSL/Linux Python. WSL's pywinauto has
no `uia` backend and cannot see Windows windows, Ableton included.

Install (Windows side):
    python -m pip install pywinauto

Usage:
    python ableton_click_proof.py
    python ableton_click_proof.py --catalog "C:\\path\\to\\control_catalog.json"
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone

TARGET_AUTOMATION_ID = "TrackView.Device[0].TitleBar.ExtendViewButton"
TARGET_NAME = "Sidechain Toggle"
TITLE_CHECK_ID = "TrackView.Device[0].TitleBar.device_title"
EXPECTED_DEVICE_TITLE = "Auto Filter"


def log(trail, msg):
    stamp = datetime.now(timezone.utc).isoformat()
    line = f"[{stamp}] {msg}"
    print(line)
    trail.append({"time": stamp, "message": msg})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalog",
        default="dumps/control_catalog.json",
        help="Path to control_catalog.json (only used to confirm the "
             "target id/name pairing before touching the live app).",
    )
    parser.add_argument(
        "--out",
        default="ableton_click_proof_result.json",
        help="Where to write the trail/result JSON.",
    )
    args = parser.parse_args()

    trail = []
    result = {
        "target_automation_id": TARGET_AUTOMATION_ID,
        "target_name": TARGET_NAME,
        "success": False,
        "reason": None,
        "device_title_seen": None,
        "toggle_state_before": None,
        "toggle_state_after": None,
        "trail": trail,
    }

    # --- Step 0: sanity-check the catalog agrees with what we're about to click
    try:
        with open(args.catalog, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        ctx = catalog["contexts"]["Auto Filter"]
        ids_in_catalog = {c["automation_id"] for c in ctx["controls"] if c["automation_id"]}
        if TARGET_AUTOMATION_ID not in ids_in_catalog:
            log(trail, f"WARNING: {TARGET_AUTOMATION_ID} not found in catalog's "
                        f"'Auto Filter' context. Proceeding anyway, but the "
                        f"catalog and this script may be out of sync.")
        else:
            log(trail, f"Catalog check OK: '{TARGET_NAME}' -> {TARGET_AUTOMATION_ID} "
                        f"confirmed present in control_catalog.json.")
    except Exception as e:
        log(trail, f"Could not read catalog at '{args.catalog}' ({e}). "
                    f"Continuing without the pre-check.")

    # --- Step 1: import pywinauto (fails loudly and clearly if run under WSL)
    try:
        from pywinauto import Desktop
    except ImportError:
        result["reason"] = "pywinauto not installed. Run: python -m pip install pywinauto"
        log(trail, result["reason"])
        write_result(args.out, result)
        sys.exit(1)

    def iter_all_elements(root, max_depth=25):
        """
        Manually walk the UIA tree via .children() (immediate children,
        recursively) instead of .descendants().

        Why: pywinauto's descendants() does FindAll(TreeScope_Descendants,
        TrueCondition) in one shot. Against a large/complex tree like
        Ableton's (thousands of elements), that single call frequently
        raises a COMError -- and pywinauto's _get_elements() SILENTLY
        SWALLOWS that error and returns an empty list, with no exception
        bubbling up. Net effect: descendants() looks like it ran fine but
        reports "0 elements found", indistinguishable from an empty tree.

        This project's own proven-working script (dump_ableton_pywinauto.py)
        never calls descendants() for exactly this reason -- it walks via
        children() layer by layer, which is far more reliable against big
        trees. We do the same here.
        """
        stack = [(root, 0)]
        while stack:
            node, depth = stack.pop()
            yield node
            if depth >= max_depth:
                continue
            try:
                kids = node.children()
            except Exception:
                kids = []
            for kid in kids:
                stack.append((kid, depth + 1))

    def find_by_auto_id(window, auto_id):
        """Return descendant elements (via manual tree walk) whose
        automation_id matches."""
        matches = []
        for elem in iter_all_elements(window):
            try:
                if elem.element_info.automation_id == auto_id:
                    matches.append(elem)
            except Exception:
                continue
        return matches

    def ensure_window_ready(window, maximize=True):
        """
        Restore/focus/maximize the Ableton window before walking its UIA
        tree. Ableton's Session/Device views are UI-virtualized -- a
        control that isn't actually rendered on screen (window minimized,
        too small, unfocused/backgrounded) simply doesn't exist as a UIA
        element yet, even though its automation_id is well-defined once
        it IS visible. This is the same lesson baked into
        dump_ableton_pywinauto.py / automate_ableton_task.py elsewhere in
        this project -- ported here since this script is standalone.
        """
        try:
            if window.is_minimized():
                log(trail, "Window is minimized; restoring...")
                window.restore()
        except Exception:
            pass
        try:
            window.set_focus()
        except Exception:
            pass
        if maximize:
            try:
                window.maximize()
            except Exception:
                pass
        time.sleep(0.3)  # give the redraw a moment before we walk the tree

    # --- Step 2: find the live Ableton window
    try:
        win = Desktop(backend="uia").window(title_re=".*Ableton Live.*")
        win.wait("exists enabled visible ready", timeout=10)
        log(trail, f"Found Ableton window: '{win.window_text()}'")
        ensure_window_ready(win)
        log(trail, "Window restored/focused/maximized before walking the UIA tree.")
    except Exception as e:
        result["reason"] = (
            f"Could not find/connect to an Ableton window ({e}). "
            f"Is Ableton open? Are you running this under WINDOWS Python, "
            f"not WSL?"
        )
        log(trail, result["reason"])
        write_result(args.out, result)
        sys.exit(1)

    # --- Step 2b: DIAGNOSTIC -- how many elements does the tree walk even
    # see, and how many of those carry a non-empty automation_id at all?
    # This tells us whether the problem is "wrong id" vs. "tree walk is
    # seeing almost nothing" (focus/rendering/backend issue).
    try:
        all_descendants = list(iter_all_elements(win))
        total_count = len(all_descendants)
        with_auto_id = []
        for elem in all_descendants:
            try:
                aid = elem.element_info.automation_id
                if aid:
                    with_auto_id.append(aid)
            except Exception:
                continue
        result["diagnostic_total_descendants"] = total_count
        result["diagnostic_with_automation_id_count"] = len(with_auto_id)
        result["diagnostic_sample_automation_ids"] = with_auto_id[:40]
        log(trail, f"DIAGNOSTIC: tree walk saw {total_count} total elements, "
                    f"{len(with_auto_id)} of them carry a non-empty automation_id.")
        if with_auto_id:
            log(trail, "DIAGNOSTIC sample automation_ids: " + ", ".join(with_auto_id[:15]))
        # Also check specifically for anything starting with "TrackView"
        trackview_ids = [a for a in with_auto_id if a.startswith("TrackView")]
        result["diagnostic_trackview_ids"] = trackview_ids[:40]
        log(trail, f"DIAGNOSTIC: {len(trackview_ids)} automation_ids start with 'TrackView'.")
        if trackview_ids:
            log(trail, "DIAGNOSTIC TrackView ids: " + ", ".join(trackview_ids[:20]))
    except Exception as e:
        log(trail, f"DIAGNOSTIC step failed: {e}")

    # --- Step 3: confirm the loaded device is actually Auto Filter
    try:
        title_elem = find_by_auto_id(win, TITLE_CHECK_ID)
        if title_elem:
            device_title = title_elem[0].window_text()
            result["device_title_seen"] = device_title
            log(trail, f"Device in slot 0 reports title: '{device_title}'")
            if EXPECTED_DEVICE_TITLE.lower() not in device_title.lower():
                log(trail, f"WARNING: expected '{EXPECTED_DEVICE_TITLE}' in "
                            f"device slot 0, but saw '{device_title}'. "
                            f"Load Auto Filter as the first device on the "
                            f"selected track and re-run.")
        else:
            log(trail, "Could not read device title element -- continuing anyway.")
    except Exception as e:
        log(trail, f"Non-fatal: title check failed ({e}). Continuing.")

    # --- Step 4: locate the target control by automation_id
    try:
        elems = find_by_auto_id(win, TARGET_AUTOMATION_ID)
        if not elems:
            result["reason"] = (
                f"'{TARGET_NAME}' (id={TARGET_AUTOMATION_ID}) not found live. "
                f"Most likely Auto Filter isn't loaded as the first device on "
                f"the currently selected track."
            )
            log(trail, result["reason"])
            write_result(args.out, result)
            sys.exit(1)
        target = elems[0]
        log(trail, f"Located '{TARGET_NAME}' live via automation_id.")
    except Exception as e:
        result["reason"] = f"Error locating target element: {e}"
        log(trail, result["reason"])
        write_result(args.out, result)
        sys.exit(1)

    # --- Step 5: read state BEFORE
    try:
        before = target.get_toggle_state()  # 0 = off, 1 = on
        result["toggle_state_before"] = before
        log(trail, f"Toggle state BEFORE click: {before}")
    except Exception as e:
        result["reason"] = f"Could not read toggle state before click: {e}"
        log(trail, result["reason"])
        write_result(args.out, result)
        sys.exit(1)

    # --- Step 6: click it
    log(trail, "Clicking the control now...")
    target.click_input()
    time.sleep(0.5)  # let Ableton's UI settle

    # --- Step 7: read state AFTER
    try:
        elems_after = find_by_auto_id(win, TARGET_AUTOMATION_ID)
        after = elems_after[0].get_toggle_state() if elems_after else None
        result["toggle_state_after"] = after
        log(trail, f"Toggle state AFTER click: {after}")
    except Exception as e:
        result["reason"] = f"Could not read toggle state after click: {e}"
        log(trail, result["reason"])
        write_result(args.out, result)
        sys.exit(1)

    # --- Step 8: verdict
    if before is not None and after is not None and before != after:
        result["success"] = True
        result["reason"] = "State flipped after click -- automation_id resolves and controls the real element."
        log(trail, "PROOF CONFIRMED: state changed after the click.")
    else:
        result["success"] = False
        result["reason"] = f"State did not change (before={before}, after={after})."
        log(trail, "State did not change -- click landed but had no observable effect, or read failed.")

    write_result(args.out, result)
    print(f"\nResult written to: {args.out}")
    sys.exit(0 if result["success"] else 1)


def write_result(path, result):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
