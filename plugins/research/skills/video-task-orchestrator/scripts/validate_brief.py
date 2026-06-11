#!/usr/bin/env python3
"""Validate that a video research brief includes required sections."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = [
    "Source summary",
    "User goal",
    "Relevant segments",
    "Required tools",
    "Required inputs",
    "Step-by-step procedure",
    "Settings, parameters, commands, or menu paths",
    "Visual checkpoints",
    "Failure modes",
    "Missing or ambiguous instructions",
    "Evidence table",
    "Conjecture and assumptions",
]


def normalize_heading(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def extract_headings(content: str) -> set[str]:
    return {
        normalize_heading(match.group("heading"))
        for match in re.finditer(r"^#{1,6}\s+(?P<heading>.+?)\s*$", content, re.MULTILINE)
    }


def validate_brief(path: Path) -> list[str]:
    headings = extract_headings(path.read_text(encoding="utf-8"))
    return [
        heading
        for heading in REQUIRED_HEADINGS
        if normalize_heading(heading) not in headings
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path, help="Research brief Markdown path")
    args = parser.parse_args()

    missing = validate_brief(args.brief)
    if missing:
        print("Missing required headings:")
        for heading in missing:
            print(f"- {heading}")
        sys.exit(1)
    print("Brief is valid.")


if __name__ == "__main__":
    main()
