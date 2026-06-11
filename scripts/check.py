#!/usr/bin/env python3
"""Validate source plugin manifests and generated marketplace artifacts."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

from build_marketplaces import build


def read_json(path: Path) -> object:
	with path.open("r", encoding="utf-8") as file:
		return json.load(file)


def require_file(path: Path) -> None:
	if not path.is_file():
		raise ValueError(f"Missing expected file: {path}")


def check_plugin_artifacts(root: Path, plugin_id: str) -> None:
	plugin_root = root / "plugins" / plugin_id
	require_file(plugin_root / ".codex-plugin" / "plugin.json")
	require_file(plugin_root / ".claude-plugin" / "plugin.json")
	read_json(plugin_root / ".codex-plugin" / "plugin.json")
	read_json(plugin_root / ".claude-plugin" / "plugin.json")


def check() -> None:
	with tempfile.TemporaryDirectory() as directory:
		output = Path(directory) / "marketplace"
		plugins = build(
			plugins_dir=Path("plugins"),
			output=output,
			marketplace_name="llm-toolbox",
			owner_name="llm-toolbox",
			category="Productivity",
		)
		require_file(output / ".agents" / "plugins" / "marketplace.json")
		require_file(output / ".claude-plugin" / "marketplace.json")
		read_json(output / ".agents" / "plugins" / "marketplace.json")
		read_json(output / ".claude-plugin" / "marketplace.json")
		for plugin in plugins:
			check_plugin_artifacts(output, plugin.id)


def main() -> None:
	check()
	print("Marketplace source and generated artifacts are valid.")


if __name__ == "__main__":
	main()
