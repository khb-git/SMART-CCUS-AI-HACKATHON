"""
Docket scraper for EPA Class VI permit pages.

Walks one or more docket pages, finds every link to a downloadable file
(PDF, DOCX, XLSX, etc.), grabs the summary text from the surrounding HTML
context, and writes a JSON manifest the RAG pipeline can consume.

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
DOWNLOADABLE_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls"}

# Polite scraping defaults — EPA is a public site but we still don't want
# to hammer it. One request per second per host is the conservative norm.
DEFAULT_REQUEST_DELAY_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_USER_AGENT = (
    "NittCarb-AI-Scraper/0.1 (research; contact: team@nittcarb.local)"
)

# Data class for representing a downloadable file found on a docket page.
@dataclass
class FileEntry:
    """One downloadable file found on a docket page."""

    summary: str       # description text from the page (what the file is about)
    url: str           # direct, absolute URL to the file
    source_page: str   # URL of the page where the link was found

# Helper functions
def fetch_page(url: str, session: requests.Session, timeout: int) -> str:
    """Fetch the HTML for one page. Raises on HTTP errors."""
    logger.info("Fetching %s", url)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text

# Check if a link is to a downloadable file
def is_downloadable(href: str) -> bool:
    """True if the href looks like a downloadable document."""
    if not href:
        return False
    # Strip query string and fragment before checking extension
    path = urlparse(href).path.lower()
    return any(path.endswith(ext) for ext in DOWNLOADABLE_EXTENSIONS)

# Extract the summary text from a file link
def extract_summary(link: Tag) -> str:
    """Get the descriptive text surrounding a file link.

    EPA pages typically present file links in one of these patterns:

      1. <a>Title</a> (PDF)(N pp, KB, Date) Description paragraph...
      2. <p>Description text <a>Title</a> (PDF)</p>
      3. <li><a>Title</a> - Description</li>

    Strategy: take the link's own text plus the text of its parent element,
    minus the parenthetical file metadata noise. This is a heuristic — if
    teammate finds it produces bad summaries on specific pages, we tune
    per-page rather than trying to invent a universal parser.
    """
    link_text = link.get_text(strip=True)

    # Walk up to the nearest "block" parent (paragraph, list item, div)
    # to find the surrounding context.
    parent = link.parent
    while parent and parent.name not in {"p", "li", "td", "div", "section"}:
        parent = parent.parent

    if parent is None:
        return link_text

    parent_text = parent.get_text(separator=" ", strip=True)

    # If the parent text is much longer than the link text, the extra is
    # probably the summary. If they're roughly equal, the link IS the summary.
    if len(parent_text) > len(link_text) + 10:
        return parent_text
    return link_text

# Scrape a single page for downloadable files.
def scrape_page(
    url: str,
    session: requests.Session,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> list[FileEntry]:
    """Scrape one docket page and return all downloadable file entries."""
    html = fetch_page(url, session, timeout)
    soup = BeautifulSoup(html, "html.parser")

    entries: list[FileEntry] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not is_downloadable(href):
            continue

        absolute_url = urljoin(url, href)

        # Deduplicate within a single page — sometimes the same file is
        # linked multiple times (e.g., in a sidebar AND in the body).
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
    output_path: Path,
    request_delay: float = DEFAULT_REQUEST_DELAY_SECONDS,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str = DEFAULT_USER_AGENT,
    retries: int = 3,
    backoff_factor: float = 0.5,
) -> int:
    """Scrape multiple pages and write a combined JSON manifest.

    Returns the number of file entries written.
    """
    session = build_retry_session(
        retries=retries,
        backoff_factor=backoff_factor,
        user_agent=user_agent,
    )

    all_entries: list[FileEntry] = []
    for i, url in enumerate(urls):
        if i > 0:
            time.sleep(request_delay)  # politeness between requests
        try:
            all_entries.extend(scrape_page(url, session, timeout))
        except requests.RequestException as exc:
            logger.error("Failed to scrape %s: %s", url, exc)
            # Continue with remaining pages — one broken URL shouldn't
            # nuke the whole manifest.

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([asdict(e) for e in all_entries], indent=2),
        encoding="utf-8",
    )
    logger.info("Wrote %d entries to %s", len(all_entries), output_path)
    return len(all_entries)

# Parse command-line arguments.
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape EPA Class VI docket pages into a JSON manifest.",
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="One or more docket page URLs to scrape.",
    )
    parser.add_argument(
        "--urls-file",
        type=Path,
        help="File containing one URL per line (alternative to positional URLs).",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("data/manifest.json"),
        help="Where to write the JSON manifest. Default: data/manifest.json",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_REQUEST_DELAY_SECONDS,
        help="Seconds to wait between requests. Default: 1.0",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Request timeout in seconds. Default: 30",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retries for transient HTTP failures. Default: 3",
    )
    parser.add_argument(
        "--backoff",
        type=float,
        default=0.5,
        help="Retry backoff factor. Default: 0.5",
    )
    parser.add_argument(
        "--render-js",
        action="store_true",
        help="Reserved for future JavaScript-rendered pages. Not implemented yet.",
    )
    return parser.parse_args(argv)

# Main entry point for the scraper.
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Collect URLs from positional args + --urls-file
    urls: list[str] = list(args.urls)
    if args.urls_file:
        urls.extend(
            line.strip()
            for line in args.urls_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

    if not urls:
        print("Error: provide at least one URL (positional or via --urls-file).",
              file=sys.stderr)
        return 1

    if args.render_js:
        print(
            "Error: --render-js is planned but not implemented yet. "
            "Current scraper supports server-rendered HTML pages only.",
            file=sys.stderr,
        )
        return 2

    count = scrape_pages(
        urls,
        args.output,
        request_delay=args.delay,
        timeout=args.timeout,
        retries=args.retries,
        backoff_factor=args.backoff,
    )
    print(f"Wrote {count} file entries to {args.output}")
    return 0

# Build a requests session with retry logic.
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


if __name__ == "__main__":
    sys.exit(main())
