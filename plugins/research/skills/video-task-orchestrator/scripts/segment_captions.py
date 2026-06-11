#!/usr/bin/env python3
"""Create compact timestamped segments from normalized captions and optional chapters."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import TypedDict


SPACE_RE = re.compile(r"\s+")


class CaptionEntry(TypedDict):
    start_seconds: float
    end_seconds: float
    text: str


class Chapter(TypedDict):
    start_seconds: float
    end_seconds: float
    title: str


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def as_caption_entries(payload: object) -> list[CaptionEntry]:
    if not isinstance(payload, dict):
        raise ValueError("Caption payload must be an object")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Caption payload must include an entries array")
    return [
        {
            "start_seconds": float(entry["start_seconds"]),
            "end_seconds": float(entry["end_seconds"]),
            "text": str(entry["text"]),
        }
        for entry in entries
        if isinstance(entry, dict)
        and "start_seconds" in entry
        and "end_seconds" in entry
        and "text" in entry
    ]


def as_chapters(payload: object) -> list[Chapter]:
    if not isinstance(payload, dict):
        return []
    chapters = payload.get("chapters")
    if not isinstance(chapters, list):
        return []
    return [
        {
            "start_seconds": float(chapter["start_seconds"]),
            "end_seconds": float(chapter["end_seconds"]),
            "title": str(chapter.get("title", "Chapter")),
        }
        for chapter in chapters
        if isinstance(chapter, dict)
        and "start_seconds" in chapter
        and "end_seconds" in chapter
    ]


def summarize(entries: list[CaptionEntry], limit: int) -> str:
    text = SPACE_RE.sub(" ", " ".join(entry["text"] for entry in entries)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rsplit(" ", 1)[0] + "..."


def label_from_summary(summary: str, fallback: str) -> str:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", summary)
    label = " ".join(words[:8])
    return label if label else fallback


def entries_in_range(
    entries: list[CaptionEntry],
    start_seconds: float,
    end_seconds: float,
) -> list[CaptionEntry]:
    return [
        entry
        for entry in entries
        if entry["end_seconds"] > start_seconds and entry["start_seconds"] < end_seconds
    ]


def chapter_segments(
    entries: list[CaptionEntry],
    chapters: list[Chapter],
    summary_limit: int,
) -> list[dict[str, object]]:
    return [
        {
            "id": f"seg-{index + 1:03d}",
            "start_seconds": chapter["start_seconds"],
            "end_seconds": chapter["end_seconds"],
            "label": chapter["title"],
            "summary": summarize(
                entries_in_range(entries, chapter["start_seconds"], chapter["end_seconds"]),
                summary_limit,
            ),
            "evidence": [
                {
                    "type": "chapter",
                    "start_seconds": chapter["start_seconds"],
                    "end_seconds": chapter["end_seconds"],
                    "source_file": "chapters.json",
                }
            ],
        }
        for index, chapter in enumerate(chapters)
    ]


def window_ranges(entries: list[CaptionEntry], window_seconds: int) -> list[tuple[float, float]]:
    if not entries:
        return []
    start = entries[0]["start_seconds"]
    end = entries[-1]["end_seconds"]
    window_count = int((end - start) // window_seconds) + 1
    return [
        (start + index * window_seconds, min(start + (index + 1) * window_seconds, end))
        for index in range(window_count)
    ]


def window_segments(
    entries: list[CaptionEntry],
    window_seconds: int,
    summary_limit: int,
) -> list[dict[str, object]]:
    segments: list[dict[str, object]] = []
    for index, (start_seconds, end_seconds) in enumerate(window_ranges(entries, window_seconds)):
        segment_entries = entries_in_range(entries, start_seconds, end_seconds)
        summary = summarize(segment_entries, summary_limit)
        if not summary:
            continue
        segments.append(
            {
                "id": f"seg-{len(segments) + 1:03d}",
                "start_seconds": round(start_seconds, 3),
                "end_seconds": round(end_seconds, 3),
                "label": label_from_summary(summary, f"Caption window {index + 1}"),
                "summary": summary,
                "evidence": [
                    {
                        "type": "caption",
                        "start_seconds": round(start_seconds, 3),
                        "end_seconds": round(end_seconds, 3),
                        "source_file": "captions.normalized.json",
                    }
                ],
            }
        )
    return segments


def write_markdown(path: Path, video_id: str, segments: list[dict[str, object]]) -> None:
    lines = [f"# Segments for {video_id}", ""]
    for segment in segments:
        lines.extend(
            [
                f"## {segment['id']}: {segment['label']}",
                f"- Time: {segment['start_seconds']}s-{segment['end_seconds']}s",
                f"- Summary: {segment['summary']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def segment_captions(
    captions_path: Path,
    output_dir: Path,
    video_id: str,
    chapters_path: Path | None,
    window_seconds: int,
    summary_limit: int,
) -> None:
    entries = as_caption_entries(load_json(captions_path))
    chapters = as_chapters(load_json(chapters_path)) if chapters_path and chapters_path.exists() else []
    segments = (
        chapter_segments(entries, chapters, summary_limit)
        if chapters
        else window_segments(entries, window_seconds, summary_limit)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"video_id": video_id, "segments": segments}
    (output_dir / "segments.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown(output_dir / "segments.md", video_id, segments)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captions", type=Path, help="captions.normalized.json path")
    parser.add_argument("output_dir", type=Path, help="Directory for segments.json and segments.md")
    parser.add_argument("--video-id", required=True, help="Video ID or source label")
    parser.add_argument("--chapters", type=Path, help="Optional chapters.json path")
    parser.add_argument("--window-seconds", type=int, default=180)
    parser.add_argument("--summary-limit", type=int, default=360)
    args = parser.parse_args()

    segment_captions(
        captions_path=args.captions,
        output_dir=args.output_dir,
        video_id=args.video_id,
        chapters_path=args.chapters,
        window_seconds=args.window_seconds,
        summary_limit=args.summary_limit,
    )


if __name__ == "__main__":
    main()
