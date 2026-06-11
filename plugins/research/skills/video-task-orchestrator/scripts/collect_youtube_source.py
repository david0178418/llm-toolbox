#!/usr/bin/env python3
"""Collect YouTube metadata and captions into the research artifact layout."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def default_task_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(".research-work") / f"task-{stamp}"


def video_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "youtu.be" in host:
        value = parsed.path.strip("/").split("/")[0]
        return value or "unknown-video"
    query_id = parse_qs(parsed.query).get("v", [""])[0]
    if query_id:
        return query_id
    match = re.search(r"/(?:shorts|embed|live)/([^/?#]+)", parsed.path)
    return match.group(1) if match else re.sub(r"[^A-Za-z0-9_-]+", "-", url).strip("-")[:80]


def run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def load_ytdlp_metadata(url: str) -> tuple[dict[str, object] | None, str | None]:
    if shutil.which("yt-dlp") is None:
        return None, "yt-dlp is not installed or not on PATH."
    result = run_command(["yt-dlp", "--dump-single-json", "--skip-download", url])
    if result.returncode != 0:
        return None, result.stderr.strip() or result.stdout.strip() or "yt-dlp metadata collection failed."
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        return None, f"yt-dlp returned invalid JSON: {error}"
    return payload if isinstance(payload, dict) else None, None


def choose_caption(info: dict[str, object], preferred_language: str) -> tuple[str | None, str]:
    subtitles = info.get("subtitles")
    automatic = info.get("automatic_captions")
    human_languages = subtitles.keys() if isinstance(subtitles, dict) else []
    automatic_languages = automatic.keys() if isinstance(automatic, dict) else []
    if preferred_language in human_languages:
        return preferred_language, "human"
    if preferred_language in automatic_languages:
        return preferred_language, "automatic"
    first_human = next(iter(human_languages), None)
    if isinstance(first_human, str):
        return first_human, "human"
    first_auto = next(iter(automatic_languages), None)
    if isinstance(first_auto, str):
        return first_auto, "automatic"
    return None, "unavailable"


def compact_metadata(
    url: str,
    video_id: str,
    info: dict[str, object] | None,
    caption_language: str | None,
    caption_status: str,
) -> dict[str, object]:
    if info is None:
        return {
            "source_type": "youtube",
            "video_id": video_id,
            "url": url,
            "caption_status": caption_status,
            "caption_language": caption_language,
            "collector": "yt-dlp",
        }
    return {
        "source_type": "youtube",
        "video_id": str(info.get("id") or video_id),
        "url": url,
        "title": str(info.get("title") or ""),
        "channel": str(info.get("channel") or info.get("uploader") or ""),
        "duration_seconds": info.get("duration"),
        "upload_date": str(info.get("upload_date") or ""),
        "description": str(info.get("description") or ""),
        "caption_status": caption_status,
        "caption_language": caption_language,
        "collector": "yt-dlp",
    }


def write_chapters(source_dir: Path, info: dict[str, object] | None) -> None:
    raw_chapters = info.get("chapters") if info else None
    chapters = raw_chapters if isinstance(raw_chapters, list) else []
    normalized = [
        {
            "start_seconds": chapter.get("start_time"),
            "end_seconds": chapter.get("end_time"),
            "title": chapter.get("title", "Chapter"),
        }
        for chapter in chapters
        if isinstance(chapter, dict)
        and chapter.get("start_time") is not None
        and chapter.get("end_time") is not None
    ]
    (source_dir / "chapters.json").write_text(
        json.dumps({"chapters": normalized}, indent=2) + "\n",
        encoding="utf-8",
    )


def fetch_caption(url: str, source_dir: Path, language: str, automatic: bool) -> str | None:
    if shutil.which("yt-dlp") is None:
        return "yt-dlp is not installed or not on PATH."
    args = [
        "yt-dlp",
        "--skip-download",
        "--sub-langs",
        language,
        "--sub-format",
        "vtt",
        "--output",
        "captions",
    ]
    args.extend(["--write-auto-subs"] if automatic else ["--write-subs"])
    args.append(url)
    result = run_command(args, cwd=source_dir)
    if result.returncode != 0:
        return result.stderr.strip() or result.stdout.strip() or "caption download failed."
    candidates = sorted(source_dir.glob("captions*.vtt"))
    if not candidates:
        return "caption download reported success but no .vtt file was created."
    candidates[0].replace(source_dir / "captions.vtt")
    for extra in candidates[1:]:
        extra.unlink(missing_ok=True)
    return None


def collect_url(url: str, task_dir: Path, preferred_language: str) -> None:
    video_id = video_id_from_url(url)
    source_dir = task_dir / "sources" / f"youtube-{video_id}"
    source_dir.mkdir(parents=True, exist_ok=True)

    log_lines = [f"# Source log: youtube-{video_id}", "", f"- URL: {url}"]
    info, metadata_error = load_ytdlp_metadata(url)
    if metadata_error:
        log_lines.append(f"- Metadata: failed - {metadata_error}")
    else:
        log_lines.append("- Metadata: collected")

    caption_language, caption_status = choose_caption(info or {}, preferred_language)
    metadata = compact_metadata(url, video_id, info, caption_language, caption_status)
    (source_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    write_chapters(source_dir, info)

    if caption_language is None:
        log_lines.append("- Captions: unavailable")
    else:
        caption_error = fetch_caption(
            url=url,
            source_dir=source_dir,
            language=caption_language,
            automatic=caption_status == "automatic",
        )
        if caption_error:
            log_lines.append(f"- Captions: failed - {caption_error}")
        else:
            log_lines.append(f"- Captions: collected ({caption_status}, {caption_language})")

    (source_dir / "source-log.md").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="YouTube URLs")
    parser.add_argument("--task-dir", type=Path, default=default_task_dir())
    parser.add_argument("--language", default="en", help="Preferred caption language")
    args = parser.parse_args()

    args.task_dir.mkdir(parents=True, exist_ok=True)
    for directory in ("sources", "analysis", "briefs", "outputs", "logs"):
        (args.task_dir / directory).mkdir(exist_ok=True)
    for url in args.urls:
        collect_url(url, args.task_dir, args.language)

    print(args.task_dir)


if __name__ == "__main__":
    main()
