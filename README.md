# LLM Toolbox

Canonical source for shareable agent plugins lives under `plugins/`.

Generated marketplace output does not belong on `main`. Build it locally with:

```bash
python3 scripts/build_marketplaces.py
```

The generated tree is written to `dist/marketplace/` and is intended to be pushed to the `marketplace` branch by CI.

Validate the source manifests and generated marketplace JSON with:

```bash
python3 scripts/check.py
```

## Install From The Marketplace Branch

Codex:

```bash
codex plugin marketplace add david017841/llm-toolbox --ref marketplace --sparse .agents/plugins --sparse plugins
```

Claude Code:

```bash
claude plugin marketplace add david017841/llm-toolbox@marketplace --sparse .claude-plugin plugins
```

Grok reads Claude Code marketplaces and plugins, so use the Claude-compatible marketplace branch unless a Grok-native package format becomes necessary.

## Source Layout

Each source plugin has this shape:

```text
plugins/
	plugin-id/
		plugin.json
		skills/
			skill-id/
				SKILL.md
```

`plugin.json` is the internal source manifest. The build script converts it into target-specific manifests:

- Codex plugin manifest: `plugins/<id>/.codex-plugin/plugin.json`
- Codex marketplace: `.agents/plugins/marketplace.json`
- Claude plugin manifest: `plugins/<id>/.claude-plugin/plugin.json`
- Claude marketplace: `.claude-plugin/marketplace.json`

The generated branch intentionally contains build artifacts. `main` should only contain source manifests, plugin content, build scripts, docs, and CI.
