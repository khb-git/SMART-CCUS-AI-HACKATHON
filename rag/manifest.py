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
import time
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 60
DEFAULT_DOWNLOAD_DELAY_SECONDS = 1.0
DEFAULT_DOWNLOAD_RETRIES = 3
DEFAULT_DOWNLOAD_BACKOFF = 0.5
DEFAULT_USER_AGENT = (
    "NittCarb-AI-Scraper/0.1 (research; contact: team@nittcarb.local)"
)


def build_retry_session(
    retries: int = DEFAULT_DOWNLOAD_RETRIES,
    backoff_factor: float = DEFAULT_DOWNLOAD_BACKOFF,
    user_agent: str = DEFAULT_USER_AGENT,
) -> requests.Session:
    """Create a requests session with retry logic for transient download failures."""
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})

    retry_strategy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("HEAD", "GET", "OPTIONS"),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

@dataclass
class ManifestEntry:
    """One entry from the scraper's JSON manifest."""

    summary: str
    url: str
    source_page: str = ""
    local_path: str = ""  # populated after download

    def filename_from_url(self, unique: bool = True, hash_length: int = 12) -> str:
        """Derive a safe local filename from the URL.

        If unique=True, append a stable hash of the full URL so files with the
        same basename from different source paths do not overwrite each other.
        """
        path = urlparse(self.url).path
        raw_name = Path(path).name or "unnamed_file"

        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", raw_name).strip("._")
        if not safe_name:
            safe_name = "unnamed_file"

        if not unique:
            return safe_name

        file_path = Path(safe_name)
        suffix = file_path.suffix
        stem = file_path.stem or "unnamed_file"

        url_hash = hashlib.sha256(self.url.encode("utf-8")).hexdigest()[:hash_length]
        return f"{stem}__{url_hash}{suffix}"


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


def write_manifest(manifest_path, entries):
    """Write ManifestEntry objects back to the manifest JSON file.

    This is used after downloads so downstream ingestion can reuse local_path
    without needing to reconstruct filenames or re-download files.
    """
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    payload = [
        {
            "summary": entry.summary,
            "url": entry.url,
            "source_page": entry.source_page,
            "local_path": entry.local_path,
        }
        for entry in entries
    ]

    manifest_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

def download_manifest(
    manifest_path,
    dest_dir,
    timeout: int = DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
    delay: float = DEFAULT_DOWNLOAD_DELAY_SECONDS,
    retries: int = DEFAULT_DOWNLOAD_RETRIES,
    backoff_factor: float = DEFAULT_DOWNLOAD_BACKOFF,
    overwrite: bool = False,
    unique_filenames: bool = True,
    update_manifest: bool = True,
):
    """Load a manifest and download every referenced file to dest_dir.

    Each entry's local_path is populated with the saved file path. Failed
    downloads are logged and skipped so one bad file does not abort the batch.

    Args:
        manifest_path: path to the scraper-generated JSON.
        dest_dir: directory to download files into. Created if missing.
        timeout: request timeout in seconds.
        delay: polite delay between downloads in seconds.
        retries: number of retries for transient HTTP failures.
        backoff_factor: exponential backoff factor for retries.
        overwrite: if True, re-download files that already exist.

    Returns:
        list of ManifestEntry objects with local_path filled in when successful.
    """
    entries = load_manifest(manifest_path)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    session = build_retry_session(
        retries=retries,
        backoff_factor=backoff_factor,
    )

    for i, entry in enumerate(entries):
        local_path = dest_dir / entry.filename_from_url(unique=unique_filenames)

        if local_path.exists() and not overwrite:
            entry.local_path = str(local_path)
            logger.info("Skipping existing file: %s", local_path)
            continue

        if i > 0 and delay > 0:
            time.sleep(delay)

        try:
            logger.info("Downloading %s", entry.url)
            response = session.get(entry.url, stream=True, timeout=timeout)
            response.raise_for_status()

            with local_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            entry.local_path = str(local_path)
            logger.info("Saved %s", local_path)

        except requests.RequestException as exc:
            logger.error("Failed to download %s: %s", entry.url, exc)
            entry.local_path = ""

    if update_manifest:
        write_manifest(manifest_path, entries)

    return entries
