"""EPA docket scraper utilities for building a local document manifest.

The scraper is intentionally small and deterministic enough for tests. It finds
downloadable PDF/DOCX/XLSX links on docket pages and writes a JSON manifest used
by the ingestion/RAG pipeline.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DOWNLOADABLE_EXTENSIONS = (".pdf", ".docx", ".xlsx")


def is_downloadable(href: str) -> bool:
    """Return whether a URL points to a supported downloadable document."""
    if not href:
        return False

    parsed = urlparse(href)
    path = parsed.path.lower()

    return path.endswith(DOWNLOADABLE_EXTENSIONS)


def extract_summary(link) -> str:
    """Extract a human-readable summary for one BeautifulSoup link."""
    link_text = " ".join(link.get_text(" ", strip=True).split())

    parent_text = ""
    parent = getattr(link, "parent", None)

    if parent is not None:
        parent_text = " ".join(parent.get_text(" ", strip=True).split())

    if parent_text and len(parent_text) > len(link_text):
        return parent_text

    return link_text


def build_session() -> requests.Session:
    """Build a requests session with basic retry behavior."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "SMART-CCUS-Class-VI-Review-Assistant/0.1 "
                "(document manifest builder)"
            )
        }
    )

    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def scrape_pages(
    urls: list[str],
    output_path: str | Path = "data/manifest.json",
    request_delay: float = 0.5,
) -> int:
    """Scrape docket pages and write a JSON manifest.

    Returns the number of downloadable document entries written.
    """
    session = build_session()
    manifest_entries: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for page_url in urls:
        response = session.get(page_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link.get("href", "")

            if not is_downloadable(href):
                continue

            absolute_url = urljoin(page_url, href)

            if absolute_url in seen_urls:
                continue

            seen_urls.add(absolute_url)

            manifest_entries.append(
                {
                    "summary": extract_summary(link),
                    "url": absolute_url,
                    "source_page": page_url,
                }
            )

        if request_delay:
            time.sleep(request_delay)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest_entries, indent=2),
        encoding="utf-8",
    )

    return len(manifest_entries)


def main() -> None:
    """Simple CLI entry point for manual scraping."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape downloadable EPA docket documents into a JSON manifest."
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="One or more docket/page URLs to scrape.",
    )
    parser.add_argument(
        "--output",
        default="data/manifest.json",
        help="Output manifest path. Default: data/manifest.json",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.5,
        help="Delay between page requests in seconds.",
    )

    args = parser.parse_args()

    count = scrape_pages(
        urls=args.urls,
        output_path=args.output,
        request_delay=args.request_delay,
    )

    print(f"Wrote {count} manifest entries to {args.output}")


if __name__ == "__main__":
    main()