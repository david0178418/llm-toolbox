# Artifact Schema

Use this layout for each task unless the user provides another workspace:

```text
.research-work/
  task-YYYYMMDD-HHMMSS/
    request.md
    sources/
      youtube-VIDEO_ID/
        metadata.json
        chapters.json
        captions.vtt
        captions.normalized.json
        source-log.md
    analysis/
      youtube-VIDEO_ID/
        segments.json
        segments.md
    briefs/
      task-brief.md
      task-brief.json
    outputs/
    logs/
```

## Source Metadata

`metadata.json` must be compact and stable:

```json
{
  "source_type": "youtube",
  "video_id": "VIDEO_ID",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "title": "Video title",
  "channel": "Channel name",
  "duration_seconds": 123,
  "upload_date": "20260131",
  "description": "Short or full description from metadata",
  "caption_status": "human|automatic|translated|unavailable|unknown",
  "caption_language": "en",
  "collector": "yt-dlp"
}
```

Do not require every field when collection fails. Preserve the error in `source-log.md`.

## Normalized Captions

`captions.normalized.json`:

```json
{
  "source_file": "captions.vtt",
  "language": "en",
  "entries": [
    {
      "start_seconds": 12.34,
      "end_seconds": 16.78,
      "text": "Caption text with markup removed."
    }
  ]
}
```

Keep raw captions on disk. Use normalized JSON for segmentation and targeted lookups.

## Chapters

`chapters.json`:

```json
{
  "chapters": [
    {
      "start_seconds": 0,
      "end_seconds": 180,
      "title": "Setup"
    }
  ]
}
```

Chapters may come from YouTube metadata, the video description, or a user-provided source. Record the origin in `source-log.md` when known.

## Segments

`segments.json`:

```json
{
  "video_id": "VIDEO_ID",
  "segments": [
    {
      "id": "seg-001",
      "start_seconds": 0,
      "end_seconds": 182,
      "label": "Tool overview and prerequisites",
      "summary": "Introduces tools, inputs, and expected image qualities.",
      "evidence": [
        {
          "type": "caption",
          "start_seconds": 44,
          "end_seconds": 61,
          "source_file": "captions.normalized.json"
        }
      ]
    }
  ]
}
```

Segment summaries should be short. Do not place large transcript excerpts in a segment.

## Brief

Briefs may be Markdown, JSON, or both. Markdown is the default handoff format. Include the required sections listed in `SKILL.md`, and keep each concrete claim tied to timestamp evidence or explicitly marked as conjecture.
