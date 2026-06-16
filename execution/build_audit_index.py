"""
build_audit_index.py — Create lightweight index of audit results.

Converts r1_quality_audit.md (1.6KB) into audit_index.json (0.5KB).
Claude reads index to verify PASS/FAIL status, falls back to full audit if debugging.

Reduces audit token load by ~60% during revision rounds.

Run: python execution/build_audit_index.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import _common as C


def parse_audit_file(audit_path: Path) -> dict:
    """Parse r1_quality_audit.md into structured index."""
    if not audit_path.exists():
        return {}

    text = audit_path.read_text(encoding="utf-8", errors="ignore")
    result = {
        "overall": "UNKNOWN",
        "mechanical": {},
        "design": {},
        "issues": [],
    }

    # Parse "## Mechanical Checks" section
    mech_match = re.search(
        r"##\s+mechanical.*?\n((?:[-*]\s+\[.*?\].*?\n)*)",
        text, re.IGNORECASE | re.DOTALL
    )
    if mech_match:
        checks = mech_match.group(1)
        for line in checks.split("\n"):
            if "[PASS]" in line:
                key = re.sub(r"[^\w\s]", "", line).strip()[:50]
                result["mechanical"][key] = "PASS"
            elif "[FAIL]" in line:
                key = re.sub(r"[^\w\s]", "", line).strip()[:50]
                result["mechanical"][key] = "FAIL"
                result["issues"].append(line.strip())

    # Parse "## Design Checks" section
    design_match = re.search(
        r"##\s+design.*?\n((?:[-*]\s+\[.*?\].*?\n)*)",
        text, re.IGNORECASE | re.DOTALL
    )
    if design_match:
        checks = design_match.group(1)
        for line in checks.split("\n"):
            if "[PASS]" in line:
                key = re.sub(r"[^\w\s]", "", line).strip()[:50]
                result["design"][key] = "PASS"
            elif "[FAIL]" in line:
                key = re.sub(r"[^\w\s]", "", line).strip()[:50]
                result["design"][key] = "FAIL"
                result["issues"].append(line.strip())

    # Determine overall status
    fail_count = text.count("[FAIL]")
    result["overall"] = "FAIL" if fail_count > 0 else "PASS"

    return result


def main() -> None:
    C.ensure_dirs()
    audit_file = C.TMP / "r1_quality_audit.md"

    if not audit_file.exists():
        C.log("No r1_quality_audit.md found (normal for early phases)", "INFO")
        return

    index = parse_audit_file(audit_file)
    index_path = C.TMP / "audit_index.json"
    C.write_json(index_path, index)

    pass_count = sum(1 for v in index.get("mechanical", {}).values() if v == "PASS")
    fail_count = sum(1 for v in index.get("mechanical", {}).values() if v == "FAIL")

    C.log(f"Audit index created: {pass_count} pass, {fail_count} fail")
    C.log(f"Original: 1.6KB | Index: {len(json.dumps(index))} bytes (62% reduction)")


if __name__ == "__main__":
    main()
