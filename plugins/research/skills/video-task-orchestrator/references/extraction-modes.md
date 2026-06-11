# Extraction Modes

Choose one primary mode before drafting a brief. If the user request mixes modes, make the mode split explicit in the brief.

## Extraction

Use for requests like "extract the workflow" or "turn this tutorial into steps."

- Focus on prerequisites, inputs, commands, settings, ordering, checks, and outputs.
- Preserve timestamps for each concrete instruction.
- Mark unclear settings and visual-only steps as missing details.

## Evaluation

Use for requests like "is this tutorial credible or complete?"

- Assess whether instructions are reproducible, specific, internally consistent, current enough, and supported by visible or caption evidence.
- Separate observed evidence from inference.
- Do not treat confident narration as proof when settings, files, or outputs are not shown.

## Comparison

Use for two or more videos.

- Create per-video source summaries first.
- Identify consensus steps, conflicts, unique details, and quality differences.
- Keep evidence tables grouped by video ID or source label.

## Replication

Use when the user wants to reproduce the video workflow but has not asked the agent to perform the domain task yet.

- Produce an implementation brief with prerequisites, ordered steps, validation checkpoints, and likely failure modes.
- Do not execute domain-specific tools unless the user separately asks for execution.

## Domain Handoff

Use when the extracted brief will be consumed by another skill or domain workflow.

- Keep the brief self-contained enough that the domain skill does not need the video URL.
- Include artifact paths, required inputs, required tools, settings, outputs, and unresolved questions.
- If the domain skill needs more source detail, inspect only the relevant timestamp slice or segment.
