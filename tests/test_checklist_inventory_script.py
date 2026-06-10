from pathlib import Path

from scripts.export_checklist_inventory import build_inventory_markdown, write_inventory


def test_build_inventory_markdown_lists_checklist_items(tmp_path: Path):
    checklist_dir = tmp_path / "checklists"
    checklist_dir.mkdir()

    checklist_path = checklist_dir / "testing_monitoring.yaml"
    checklist_path.write_text(
        """
checklist_id: testing_monitoring
plan_type: testing_monitoring
section_id: "8"
title: Testing and Monitoring
description: Testing and monitoring checklist.
items:
  - item_id: tm_001
    label: Injection pressure monitoring
    description: Review injection pressure monitoring.
    requirement_level: required
    severity: high
  - item_id: tm_002
    label: Plume and pressure front tracking
    description: Review plume and pressure front tracking.
    requirement_level: required
    severity: high
""".strip(),
        encoding="utf-8",
    )

    markdown = build_inventory_markdown(checklist_dir)

    assert "# Current Checklist Inventory" in markdown
    assert "`testing_monitoring`" in markdown
    assert "Testing and Monitoring" in markdown
    assert "`tm_001`" in markdown
    assert "Injection pressure monitoring" in markdown
    assert "`tm_002`" in markdown
    assert "Plume and pressure front tracking" in markdown


def test_write_inventory_creates_markdown_file(tmp_path: Path):
    checklist_dir = tmp_path / "checklists"
    checklist_dir.mkdir()

    checklist_path = checklist_dir / "well_construction.yaml"
    checklist_path.write_text(
        """
checklist_id: well_construction
plan_type: well_construction
section_id: "6"
title: Well Construction
description: Well construction checklist.
items:
  - item_id: wc_001
    label: Casing and cementing
    description: Review casing and cementing information.
    requirement_level: required
    severity: high
""".strip(),
        encoding="utf-8",
    )

    output_path = tmp_path / "docs" / "checklist_inventory.md"

    write_inventory(
        checklist_dir=checklist_dir,
        output_path=output_path,
    )

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Well Construction" in content
    assert "`wc_001`" in content