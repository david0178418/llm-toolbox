#!/usr/bin/env python3
"""Build generated marketplace trees from canonical plugin source."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Plugin:
	id: str
	name: str
	version: str
	description: str
	has_skills: bool
	source_path: Path


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Build Codex and Claude marketplace artifacts.")
	parser.add_argument("--plugins-dir", default="plugins", help="Canonical plugin source directory.")
	parser.add_argument("--output", default="dist/marketplace", help="Generated marketplace output directory.")
	parser.add_argument("--marketplace-name", default="llm-toolbox", help="Marketplace identifier.")
	parser.add_argument("--owner-name", default="llm-toolbox", help="Marketplace owner display name.")
	parser.add_argument("--category", default="Productivity", help="Codex marketplace category.")
	return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
	with path.open("r", encoding="utf-8") as file:
		value = json.load(file)

	if isinstance(value, dict):
		return value

	raise ValueError(f"{path} must contain a JSON object")


def require_string(value: dict[str, Any], key: str, path: Path) -> str:
	field = value.get(key)
	if isinstance(field, str) and field:
		return field

	raise ValueError(f"{path} must define a non-empty string field: {key}")


def validate_skill(value: Any, path: Path) -> None:
	if not isinstance(value, dict):
		raise ValueError(f"{path} skills entries must be objects")

	require_string(value, "id", path)
	require_string(value, "path", path)
	require_string(value, "description", path)


def has_valid_skills(value: Any, path: Path) -> bool:
	if not isinstance(value, list):
		raise ValueError(f"{path} must define an array field: skills")

	for item in value:
		validate_skill(item, path)

	return bool(value)


def read_plugin(path: Path) -> Plugin:
	manifest_path = path / "plugin.json"
	value = read_json(manifest_path)

	return Plugin(
		id=require_string(value, "id", manifest_path),
		name=require_string(value, "name", manifest_path),
		version=require_string(value, "version", manifest_path),
		description=require_string(value, "description", manifest_path),
		has_skills=has_valid_skills(value.get("skills"), manifest_path),
		source_path=path,
	)


def discover_plugins(plugins_dir: Path) -> tuple[Plugin, ...]:
	if not plugins_dir.exists():
		raise ValueError(f"Plugin source directory does not exist: {plugins_dir}")

	plugins = tuple(
		read_plugin(path)
		for path in sorted(plugins_dir.iterdir())
		if path.is_dir() and (path / "plugin.json").exists()
	)

	if plugins:
		return plugins

	raise ValueError(f"No plugins found in {plugins_dir}")


def clean_output(output: Path) -> None:
	if output.exists():
		shutil.rmtree(output)

	output.mkdir(parents=True)


def copy_plugin_source(plugin: Plugin, target: Path) -> None:
	def ignore(_: str, names: list[str]) -> set[str]:
		return {name for name in names if name == "plugin.json" or name == "__pycache__" or name.endswith(".pyc")}

	shutil.copytree(plugin.source_path, target, ignore=ignore)


def write_json(path: Path, value: dict[str, Any]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(f"{json.dumps(value, indent='\t')}\n", encoding="utf-8")


def codex_manifest(plugin: Plugin) -> dict[str, Any]:
	value: dict[str, Any] = {
		"name": plugin.id,
		"version": plugin.version,
		"description": plugin.description,
	}

	if plugin.has_skills:
		value["skills"] = "./skills/"

	return value


def claude_manifest(plugin: Plugin) -> dict[str, Any]:
	value: dict[str, Any] = {
		"name": plugin.id,
		"description": plugin.description,
		"version": plugin.version,
	}

	if plugin.has_skills:
		value["skills"] = "./skills/"

	return value


def codex_marketplace_entry(plugin: Plugin, category: str) -> dict[str, Any]:
	return {
		"name": plugin.id,
		"source": {
			"source": "local",
			"path": f"./plugins/{plugin.id}",
		},
		"policy": {
			"installation": "AVAILABLE",
			"authentication": "ON_INSTALL",
		},
		"category": category,
		"interface": {
			"displayName": plugin.name,
			"description": plugin.description,
		},
	}


def claude_marketplace_entry(plugin: Plugin) -> dict[str, Any]:
	return {
		"name": plugin.id,
		"source": f"./plugins/{plugin.id}",
		"description": plugin.description,
	}


def write_plugin(plugin: Plugin, output: Path) -> None:
	target = output / "plugins" / plugin.id
	copy_plugin_source(plugin, target)
	write_json(target / ".codex-plugin" / "plugin.json", codex_manifest(plugin))
	write_json(target / ".claude-plugin" / "plugin.json", claude_manifest(plugin))


def write_marketplaces(
	plugins: tuple[Plugin, ...],
	output: Path,
	marketplace_name: str,
	owner_name: str,
	category: str,
) -> None:
	write_json(
		output / ".agents" / "plugins" / "marketplace.json",
		{
			"name": marketplace_name,
			"plugins": [codex_marketplace_entry(plugin, category) for plugin in plugins],
		},
	)
	write_json(
		output / ".claude-plugin" / "marketplace.json",
		{
			"name": marketplace_name,
			"owner": {
				"name": owner_name,
			},
			"description": "Shareable coding-agent plugins from llm-toolbox.",
			"plugins": [claude_marketplace_entry(plugin) for plugin in plugins],
		},
	)


def build(
	plugins_dir: Path,
	output: Path,
	marketplace_name: str,
	owner_name: str,
	category: str,
) -> tuple[Plugin, ...]:
	plugins = discover_plugins(plugins_dir)
	clean_output(output)
	for plugin in plugins:
		write_plugin(plugin, output)

	write_marketplaces(plugins, output, marketplace_name, owner_name, category)
	return plugins


def main() -> None:
	args = parse_args()
	plugins = build(
		plugins_dir=Path(args.plugins_dir),
		output=Path(args.output),
		marketplace_name=args.marketplace_name,
		owner_name=args.owner_name,
		category=args.category,
	)
	print(f"Built {len(plugins)} plugin(s) into {args.output}")


if __name__ == "__main__":
	main()
