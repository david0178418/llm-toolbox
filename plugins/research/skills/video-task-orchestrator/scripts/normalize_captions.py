#!/usr/bin/env python3
"""Normalize WebVTT captions into compact timestamped JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})"
)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def parse_timestamp(value: str) -> float:
    parts = value.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    minutes, seconds = parts
    return int(minutes) * 60 + float(seconds)


def clean_text(lines: list[str]) -> str:
    joined = " ".join(line.strip() for line in lines if line.strip())
    without_tags = TAG_RE.sub("", joined)
    return SPACE_RE.sub(" ", html.unescape(without_tags)).strip()


def parse_vtt(content: str) -> list[dict[str, float | str]]:
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n"))
    entries: list[dict[str, float | str]] = []
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        timestamp_index = next(
            (index for index, line in enumerate(lines) if TIMESTAMP_RE.search(line)),
            None,
        )
        if timestamp_index is None:
            continue
        match = TIMESTAMP_RE.search(lines[timestamp_index])
        if match is None:
            continue
        text = clean_text(lines[timestamp_index + 1 :])
        if not text:
            continue
        entries.append(
            {
                "start_seconds": round(parse_timestamp(match.group("start")), 3),
                "end_seconds": round(parse_timestamp(match.group("end")), 3),
                "text": text,
            }
        )
    return entries


def normalize_caption_file(input_path: Path, output_path: Path, language: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_file": input_path.name,
        "language": language,
        "entries": parse_vtt(input_path.read_text(encoding="utf-8")),
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Raw .vtt caption file")
    parser.add_argument("output", type=Path, help="Output normalized JSON path")
    parser.add_argument("--language", default="unknown", help="Caption language code")
    args = parser.parse_args()

    normalize_caption_file(args.input, args.output, args.language)


if __name__ == "__main__":
    main()
