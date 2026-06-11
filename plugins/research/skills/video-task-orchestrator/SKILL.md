---
name: video-task-orchestrator
description: Extract, evaluate, compare, or apply instructions from YouTube or video sources by creating local source artifacts, timestamped segments, and compact research or task briefs. Use when an agent needs to turn one or more video tutorials, walkthroughs, demos, talks, captions, or transcripts into goal-specific implementation notes without loading full transcripts into context.
---

# Video Task Orchestrator

## Core Rule

Treat video material as source artifacts on disk. Do not load a full transcript, raw caption file, or large frame note set into context by default. Load compact summaries first, then inspect narrow timestamp slices only when a specific claim, step, or ambiguity requires it.

## Workflow

1. Restate the user goal, source list, desired output, and whether the task is extraction, evaluation, comparison, replication, or domain handoff.
2. Create a task folder under `.research-work/task-YYYYMMDD-HHMMSS/` unless the user provides a different workspace.
3. Save the request in `request.md`.
4. Collect source artifacts with `scripts/collect_youtube_source.py` when the source is a YouTube URL. If live collection fails, record the failure and ask for a local transcript, caption file, or metadata artifact only if needed.
5. Normalize captions with `scripts/normalize_captions.py` when raw VTT captions are available.
6. Segment the source with `scripts/segment_captions.py`. Prefer chapters when present, otherwise use caption windows.
7. Read `segments.md` and only the relevant `segments.json` entries before drafting the brief.
8. Produce a compact brief in `briefs/` with timestamp evidence for concrete claims and explicit labels for conjecture, missing details, or likely visual-only instructions.
9. Validate the brief with `scripts/validate_brief.py` before using it as handoff material.

## Resource Map

- Read `references/artifact-schema.md` before creating or validating task folders, source artifacts, segment files, or briefs.
- Read `references/extraction-modes.md` before deciding brief emphasis or comparing multiple videos.
- Run `scripts/collect_youtube_source.py --help` for source collection arguments.
- Run `scripts/normalize_captions.py --help` for VTT normalization arguments.
- Run `scripts/segment_captions.py --help` for segmentation arguments.
- Run `scripts/validate_brief.py --help` for brief validation arguments.

## Brief Requirements

Every brief must include:

- Source summary
- User goal
- Relevant segments
- Required tools
- Required inputs
- Step-by-step procedure
- Settings, parameters, commands, or menu paths
- Visual checkpoints
- Failure modes
- Missing or ambiguous instructions
- Evidence table with timestamps
- Conjecture and assumptions

Keep briefs concise enough to load into context. Prefer timestamp citations over transcript excerpts. Quote only short source phrases when wording is essential.

## Evidence Rules

- Mark caption-derived claims as caption evidence.
- Mark chapter-derived structure as chapter evidence.
- Mark inferred steps as conjecture.
- Mark missing UI settings, visual demonstrations, or unclear tool names as uncertainty.
- For multiple videos, distinguish consensus from one-video-specific advice and identify conflicts.

## Boundary

This skill does not download full videos, transcribe audio, sample frames, automate domain tools, or execute domain workflows by default. Domain execution can consume the brief later and request a targeted follow-up lookup when the brief is insufficient.
