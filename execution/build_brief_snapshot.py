"""
build_brief_snapshot.py — Create lightweight snapshot of design brief.

Converts design_brief.md (2-3KB) into brief_snapshot.md (0.5KB).
Claude reads snapshot during code gen/revision, falls back to full brief if needed.

Reduces brief token load by ~80% per revision round.

Run: python execution/build_brief_snapshot.py
"""

from __future__ import annotations

import re
from pathlib import Path

import _common as C


def extract_palette(text: str) -> list[str]:
    """Extract color palette lines."""
    match = re.search(r"##\s+palette(.*?)(?=##|$)", text, re.IGNORECASE | re.DOTALL)
    if match:
        colors = []
        for line in match.group(1).split("\n"):
            line = line.strip()
            if line.startswith("-") and "#" in line:
                colors.append(line[2:] if line.startswith("- ") else line)
        return colors[:10]  # Max 10 colors
    return []


def extract_fonts(text: str) -> dict:
    """Extract font families."""
    fonts = {}
    match = re.search(r"##\s+fonts(.*?)(?=##|$)", text, re.IGNORECASE | re.DOTALL)
    if match:
        for line in match.group(1).split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                fonts[key.strip().lower()] = val.strip()
    return fonts


def extract_sections(text: str) -> list[str]:
    """Extract section order."""
    match = re.search(r"##\s+section[_\s]*order(.*?)(?=##|$)", text, re.IGNORECASE | re.DOTALL)
    if match:
        sections = []
        for line in match.group(1).split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove bullets/numbers
                clean = re.sub(r"^[-*\d.\s]+", "", line).strip()
                if clean:
                    sections.append(clean)
        return sections
    return []


def count_empty(text: str) -> list[str]:
    """Count EMPTY sections."""
    empties = re.findall(r"<!--\s*EMPTY:\s*([^-]+)", text)
    return [e.strip() for e in empties]


def main() -> None:
    C.ensure_dirs()
    brief_path = C.TMP / "design_brief.md"

    if not brief_path.exists():
        C.log("No design_brief.md found (normal before Gemini handoff)", "INFO")
        return

    text = brief_path.read_text(encoding="utf-8", errors="ignore")

    # Build snapshot
    snapshot_lines = [
        "# Design Brief Snapshot",
        "",
        "**Generated:** Quick reference for code generation.",
        "**Full brief:** .tmp/design_brief.md",
        "",
    ]

    # Palette
    colors = extract_palette(text)
    if colors:
        snapshot_lines.append("## Palette")
        for color in colors:
            snapshot_lines.append(f"- {color}")
        snapshot_lines.append("")

    # Fonts
    fonts = extract_fonts(text)
    if fonts:
        snapshot_lines.append("## Fonts")
        for key, val in fonts.items():
            snapshot_lines.append(f"- {key}: {val}")
        snapshot_lines.append("")

    # Section order
    sections = extract_sections(text)
    if sections:
        snapshot_lines.append("## Sections")
        for i, sec in enumerate(sections, 1):
            snapshot_lines.append(f"{i}. {sec}")
        snapshot_lines.append("")

    # Empty sections
    empties = count_empty(text)
    if empties:
        snapshot_lines.append("## EMPTY Sections (to be filled by owner)")
        for empty in empties:
            snapshot_lines.append(f"- {empty}")
        snapshot_lines.append("")

    snapshot_lines.append("---")
    snapshot_lines.append("See full `design_brief.md` for copy_by_section, image_assignments, visual_direction.")

    snapshot_content = "\n".join(snapshot_lines)
    snapshot_path = C.TMP / "brief_snapshot.md"
    snapshot_path.write_text(snapshot_content, encoding="utf-8")

    C.log(f"Brief snapshot created: {len(snapshot_content)} bytes (~80% smaller)")


if __name__ == "__main__":
    main()
