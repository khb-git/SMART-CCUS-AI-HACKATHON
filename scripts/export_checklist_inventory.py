"""
Export a Markdown inventory of the current review checklist YAML files.

This script is intentionally lightweight. It helps the team compare the
current SMART CCUS checklist schemas against EPA's Class VI completeness
checklist before making checklist-expansion changes.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CHECKLIST_DIR = Path("review") / "checklists"
DEFAULT_OUTPUT_PATH = Path("docs") / "checklist_inventory.md"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load one YAML file as a dictionary."""
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Checklist YAML must contain a dictionary: {path}")

    return data


def checklist_files(checklist_dir: Path) -> list[Path]:
    """Return sorted checklist YAML files."""
    if not checklist_dir.exists():
        raise FileNotFoundError(f"Checklist directory not found: {checklist_dir}")

    return sorted(checklist_dir.glob("*.yaml"))


def build_inventory_markdown(checklist_dir: Path) -> str:
    """Build a Markdown inventory of checklist files and items."""
    lines = [
        "# Current Checklist Inventory",
        "",
        "This file inventories the current SMART CCUS checklist YAML files.",
        "It is intended to support comparison against EPA Class VI completeness review materials.",
        "",
        "## Summary",
        "",
    ]

    files = checklist_files(checklist_dir)
    total_items = 0

    checklist_summaries = []

    for path in files:
        data = load_yaml(path)
        items = data.get("items", [])

        if not isinstance(items, list):
            raise ValueError(f"Checklist items must be a list: {path}")

        total_items += len(items)

        checklist_summaries.append(
            {
                "path": path,
                "checklist_id": data.get("checklist_id", path.stem),
                "plan_type": data.get("plan_type", path.stem),
                "title": data.get("title", path.stem),
                "item_count": len(items),
                "items": items,
            }
        )

    lines.extend(
        [
            f"- Checklist files: {len(files)}",
            f"- Checklist items: {total_items}",
            "",
            "## Checklist files",
            "",
            "| Plan type | Title | Items | File |",
            "|---|---|---:|---|",
        ]
    )

    for summary in checklist_summaries:
        lines.append(
            "| "
            f"`{summary['plan_type']}` | "
            f"{summary['title']} | "
            f"{summary['item_count']} | "
            f"`{summary['path']}` |"
        )

    lines.append("")

    for summary in checklist_summaries:
        lines.extend(
            [
                f"## {summary['title']}",
                "",
                f"- Checklist ID: `{summary['checklist_id']}`",
                f"- Plan type: `{summary['plan_type']}`",
                f"- Source file: `{summary['path']}`",
                f"- Item count: {summary['item_count']}",
                "",
                "| Item ID | Label | Requirement | Severity |",
                "|---|---|---|---|",
            ]
        )

        for item in summary["items"]:
            lines.append(
                "| "
                f"`{item.get('item_id', '')}` | "
                f"{item.get('label', '')} | "
                f"{item.get('requirement_level', '')} | "
                f"{item.get('severity', '')} |"
            )

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_inventory(checklist_dir: Path, output_path: Path) -> Path:
    """Write checklist inventory Markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_inventory_markdown(checklist_dir),
        encoding="utf-8",
    )
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export current checklist inventory to Markdown.",
    )
    parser.add_argument(
        "--checklist-dir",
        type=Path,
        default=DEFAULT_CHECKLIST_DIR,
        help="Directory containing checklist YAML files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Markdown output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = write_inventory(
        checklist_dir=args.checklist_dir,
        output_path=args.output,
    )
    print(f"Wrote checklist inventory to {output_path}")


if __name__ == "__main__":
    main()