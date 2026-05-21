"""
Manifest loader — bridges the scraper output into the RAG pipeline.

The scraper (../scraper.py) produces a JSON file like:

    [
      {"summary": "...", "url": "https://.../file.pdf", "source_page": "..."},
      ...
    ]

This module reads that manifest. Two modes:

  1. load_manifest(path) - just parses the JSON into ManifestEntry objects.
     Useful when files have already been downloaded separately.

  2. download_manifest(path, dest_dir) - parses AND downloads each file
     into dest_dir, returning entries with a local_path field populated.

Phase 2's ingestion pipeline can then iterate over the entries and call
load_pdf / load_docx on each local file.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class ManifestEntry:
    """One entry from the scraper's JSON manifest."""

    summary: str
    url: str
    source_page: str = ""
    local_path: str = ""  # populated after download

    def filename_from_url(self) -> str:
        """Derive a safe local filename from the URL."""
        path = urlparse(self.url).path
        name = Path(path).name
        return name or "unnamed_file"


def load_manifest(manifest_path):
    """Parse a scraper-generated JSON manifest into ManifestEntry objects.

    Args:
        manifest_path: path to the JSON file.

    Returns:
        list of ManifestEntry objects.

    Raises:
        FileNotFoundError: if manifest_path doesn't exist.
        ValueError: if the file isn't valid JSON or the shape is wrong.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Manifest is not valid JSON: {exc}") from exc

    if not isinstance(raw, list):
        raise ValueError(
            f"Manifest must be a JSON list, got {type(raw).__name__}"
        )

    entries = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"Manifest entry {i} is not an object")
        if "url" not in item:
            raise ValueError(f"Manifest entry {i} is missing required 'url' field")
        entries.append(ManifestEntry(
            summary=item.get("summary", ""),
            url=item["url"],
            source_page=item.get("source_page", ""),
            local_path=item.get("local_path", ""),
        ))

    logger.info("Loaded %d entries from %s", len(entries), manifest_path)
    return entries


def download_manifest(manifest_path, dest_dir):
    """Load a manifest and download every referenced file to dest_dir.

    Each entry's local_path is populated with the saved file path.

    Args:
        manifest_path: path to the scraper-generated JSON.
        dest_dir: directory to download files into. Created if missing.

    Returns:
        list of ManifestEntry objects with local_path filled in.

    TODO (Phase 2):
        - Implement using requests.get + streaming for large files.
        - Skip files that already exist locally (idempotent re-runs).
        - Polite delay between downloads (1s default).
        - Handle download failures per-file without aborting the batch.

    Sketch:
        entries = load_manifest(manifest_path)
        dest_dir = Path(dest_dir); dest_dir.mkdir(parents=True, exist_ok=True)
        session = requests.Session()
        for entry in entries:
            local = dest_dir / entry.filename_from_url()
            if local.exists():
                entry.local_path = str(local)
                continue
            try:
                resp = session.get(entry.url, stream=True, timeout=60)
                resp.raise_for_status()
                with local.open("wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                entry.local_path = str(local)
                time.sleep(1)
            except requests.RequestException as exc:
                logger.error("Failed to download %s: %s", entry.url, exc)
        return entries
    """
    entries = load_manifest(manifest_path)
    logger.warning("download_manifest not yet implemented")
    return entries
