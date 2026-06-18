"""EPA docket scraper utilities for building a local document manifest.

The scraper is intentionally small and deterministic enough for tests. It finds
downloadable PDF/DOCX/XLSX links on docket pages and writes a JSON manifest used
by the ingestion/RAG pipeline.

Output format:

    [
      {
        "summary": "EPA Seeks Comments on Plan to Modify an Existing Carbon Storage Permit",
        "url": "https://www.epa.gov/.../file.pdf",
        "source_page": "https://www.epa.gov/uic/adm-decatur-permit-documents"
      },
      ...
    ]

The output is a flat list across all scraped pages so the consumer doesn't
have to know which page a file came from — but `source_page` is preserved
so the manifest can be filtered or grouped later if needed.

Usage:

    # Scrape one page
    python scraper.py https://www.epa.gov/uic/some-docket-page

    # Scrape multiple pages, write to custom path
    python scraper.py page1_url page2_url -o data/manifest.json

    # Scrape from a list of URLs in a file (one per line)
    python scraper.py --urls-file docket_urls.txt -o data/manifest.json
"""

# Import modules
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up logging
logger = logging.getLogger(__name__)

# File extensions we treat as "downloadable documents" worth indexing.
# Add to this set if you find others in the wild (e.g. .csv, .zip).
DOWNLOADABLE_EXTENSIONS = (".pdf", ".docx", ".doc", ".xlsx", ".xls")

# Polite scraping defaults — EPA is a public site but we still don't want
# to hammer it. One request per second per host is the conservative norm.
DEFAULT_REQUEST_DELAY_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_USER_AGENT = (
    "NittCarb-AI-Scraper/0.1 (research; contact: team@nittcarb.local)"
)

# Matches EPA-style file metadata noise in summary text, e.g.:
#   (PDF)  (PDF)(5 pp, 2.3 MB, January 2024)  (2.3 MB)
_FILE_META_NOISE = re.compile(
    r"\(\s*(?:PDF|DOCX?|XLSX?|XLS)\s*\)"
    r"|\(\s*\d+\s*pp[.,\s][^)]*\)"
    r"|\(\s*[\d.,]+\s*(?:KB|MB|GB)\s*\)",
    re.IGNORECASE,
)

logger = logging.getLogger(__name__)


def clean_summary(text: str) -> str:
    """Strip file-metadata noise from a summary string."""
    return " ".join(_FILE_META_NOISE.sub("", text).split())


@dataclass
class FileEntry:
    """One downloadable file found on a docket page."""

    summary: str       # description text from the page (what the file is about)
    url: str           # direct, absolute URL to the file
    source_page: str   # URL of the page where the link was found


def build_retry_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
    user_agent: str = DEFAULT_USER_AGENT,
) -> requests.Session:
    """Create a requests session with retry logic for transient failures."""
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


def fetch_page(url: str, session: requests.Session, timeout: int) -> str:
    """Fetch the HTML for one page. Raises on HTTP errors."""
    logger.info("Fetching %s", url)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text

# Check if a link is to a downloadable file
def is_downloadable(href: str) -> bool:
    """Return whether a URL points to a supported downloadable document."""
    if not href:
        return False

    parsed = urlparse(href)
    path = parsed.path.lower()

    return path.endswith(DOWNLOADABLE_EXTENSIONS)


def extract_summary(link) -> str:
    """Extract a human-readable summary for one BeautifulSoup link.

    Walks up to the nearest block-level parent and uses its text as context,
    minus file-metadata noise. Falls back to the link's own text if there is
    no meaningful surrounding context.
    """
    link_text = link.get_text(strip=True)

    # Walk up to the nearest "block" parent (paragraph, list item, div)
    # to find the surrounding context.
    parent = link.parent
    while parent and parent.name not in {"p", "li", "td", "div", "section"}:
        parent = parent.parent

    if parent is None:
        return clean_summary(link_text)

    parent_text = parent.get_text(separator=" ", strip=True)

    # If the parent text is much longer than the link text, the extra is
    # probably the summary. If they're roughly equal, the link IS the summary.
    if len(parent_text) > len(link_text) + 10:
        return clean_summary(parent_text)
    return clean_summary(link_text)


def scrape_page(
    url: str,
    session: requests.Session,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    seen_urls: set[str] | None = None,
) -> list[FileEntry]:
    """Scrape one docket page and return all downloadable file entries.

    Pass a shared ``seen_urls`` set across multiple pages to deduplicate
    the same file appearing on more than one docket page.
    """
    html = fetch_page(url, session, timeout)
    soup = BeautifulSoup(html, "html.parser")

    entries: list[FileEntry] = []
    if seen_urls is None:
        seen_urls = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")

        if not is_downloadable(href):
            continue

        absolute_url = urljoin(url, href)

        # Deduplicate across all scraped pages so the same file linked
        # on multiple docket pages only appears once in the manifest.
        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)

        summary = extract_summary(link)
        entries.append(FileEntry(
            summary=summary,
            url=absolute_url,
            source_page=url,
        ))

    logger.info("Found %d downloadable files on %s", len(entries), url)
    return entries

# Scrape multiple pages for downloadable files.
def scrape_pages(
    urls: list[str],
    output_path: str | Path = "data/manifest.json",
    request_delay: float = DEFAULT_REQUEST_DELAY_SECONDS,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str = DEFAULT_USER_AGENT,
    retries: int = 3,
    backoff_factor: float = 0.5,
    append: bool = False,
) -> int:
    """Scrape docket pages and write a JSON manifest.

    When ``append=True`` and the output file already exists, new entries are
    merged into it rather than replacing it. URLs already in the manifest are
    skipped so the manifest stays deduplicated.

    Returns the number of file entries written to the manifest.
    """
    output_path = Path(output_path)
    session = build_retry_session(retries, backoff_factor, user_agent)

    # Shared set prevents the same URL from appearing twice whether it is
    # linked on multiple pages in this run or already in an existing manifest.
    seen_urls: set[str] = set()
    existing_entries: list[FileEntry] = []

    if append and output_path.exists():
        try:
            existing_data = json.loads(output_path.read_text(encoding="utf-8"))
            existing_entries = [FileEntry(**e) for e in existing_data]
            seen_urls.update(e.url for e in existing_entries)
            logger.info("Loaded %d existing entries for append", len(existing_entries))
        except Exception as exc:
            logger.warning("Could not load existing manifest for append: %s", exc)

    new_entries: list[FileEntry] = []
    for i, url in enumerate(urls):
        if i > 0:
            time.sleep(request_delay)  # politeness between requests
        try:
            new_entries.extend(scrape_page(url, session, timeout, seen_urls=seen_urls))
        except requests.RequestException as exc:
            logger.error("Failed to scrape %s: %s", url, exc)
            # Continue with remaining pages — one broken URL shouldn't
            # nuke the whole manifest.

    all_entries = existing_entries + new_entries

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([asdict(e) for e in all_entries], indent=2),
        encoding="utf-8",
    )

    return len(all_entries)


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
        default=DEFAULT_REQUEST_DELAY_SECONDS,
        help="Delay between page requests in seconds. Default: 1.0",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help=(
            "Merge new entries into an existing manifest instead of overwriting it. "
            "URLs already in the manifest are skipped."
        ),
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    count = scrape_pages(
        urls=args.urls,
        output_path=args.output,
        request_delay=args.request_delay,
        append=args.append,
    )
    print(f"Wrote {count} file entries to {args.output}")


if __name__ == "__main__":
    main()
