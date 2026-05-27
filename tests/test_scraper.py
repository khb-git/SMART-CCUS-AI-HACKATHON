"""
Tests for the scraper and the manifest loader that bridges it
into the RAG pipeline.

The scraper tests use BeautifulSoup against fake HTML rather than hitting
the EPA site — that keeps tests fast, deterministic, and runnable offline.
The integration with real EPA pages should be smoke-tested manually by
running the scraper against one docket URL.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from rag.manifest import ManifestEntry, load_manifest
from scraper import (
    extract_summary,
    is_downloadable,
    scrape_pages,
)


# ----- scraper: is_downloadable -----

@pytest.mark.parametrize("href,expected", [
    ("/files/permit.pdf", True),
    ("https://epa.gov/file.PDF", True),                 # case-insensitive
    ("/docs/application.docx", True),
    ("/data/results.xlsx", True),
    ("/page.html", False),
    ("https://epa.gov/uic/some-page", False),
    ("", False),
    ("https://epa.gov/file.pdf?download=1", True),      # query string OK
    ("https://epa.gov/file.pdf#section-2", True),       # fragment OK
])
def test_is_downloadable(href, expected):
    assert is_downloadable(href) == expected


# ----- scraper: extract_summary -----

def test_extract_summary_uses_parent_text_when_longer():
    """When surrounding text is meaningful, use it as the summary."""
    html = """
    <p>
      Read the application narrative for ADM Decatur:
      <a href="/files/adm.pdf">ADM Decatur Application</a>
      (PDF, 5MB)
    </p>
    """
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("a")
    summary = extract_summary(link)
    assert "ADM Decatur" in summary
    assert "narrative" in summary


def test_extract_summary_falls_back_to_link_text():
    """When the link IS the full description, use the link text."""
    html = '<li><a href="/files/spec.pdf">Well Construction Specification</a></li>'
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("a")
    summary = extract_summary(link)
    assert summary == "Well Construction Specification"


def test_extract_summary_handles_orphaned_link():
    """A link with no useful parent still gets a summary."""
    html = '<a href="/files/x.pdf">Just a link</a>'
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("a")
    summary = extract_summary(link)
    assert summary == "Just a link"


# ----- scraper: end-to-end with mocked HTTP -----

def test_scrape_pages_writes_manifest(tmp_path, monkeypatch):
    """scrape_pages produces a JSON manifest matching the expected shape."""
    fake_html = """
    <html><body>
      <p>
        First permit doc:
        <a href="/files/permit1.pdf">Permit 1 Application</a> (PDF)
      </p>
      <ul>
        <li><a href="https://example.com/docs/permit2.docx">Permit 2 Specs</a></li>
        <li><a href="/page.html">Not a downloadable file</a></li>
      </ul>
    </body></html>
    """

    class FakeResponse:
        text = fake_html
        def raise_for_status(self): pass

    class FakeSession:
        headers: dict = {}
        def get(self, url, timeout): return FakeResponse()

    # Patch requests.Session within the scraper module
    import scraper as scraper_module
    monkeypatch.setattr(scraper_module.requests, "Session", FakeSession)

    output_path = tmp_path / "manifest.json"
    count = scrape_pages(
        urls=["https://www.epa.gov/uic/fake-docket-page"],
        output_path=output_path,
        request_delay=0,  # no sleep in tests
    )

    assert count == 2  # the two downloadable files, not the .html link

    manifest = json.loads(output_path.read_text())
    assert len(manifest) == 2

    # Every entry has the minimum required shape
    for entry in manifest:
        assert "summary" in entry
        assert "url" in entry
        assert "source_page" in entry
        assert entry["url"].startswith("http")  # absolute URL

    # Relative URLs got resolved against the source page
    urls = [e["url"] for e in manifest]
    assert any("permit1.pdf" in u and u.startswith("https://www.epa.gov") for u in urls)
    assert any("permit2.docx" in u for u in urls)


# ----- manifest loader -----

def test_load_manifest_round_trip(tmp_path):
    """A manifest written by the scraper loads back into ManifestEntry objects."""
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps([
        {
            "summary": "ADM Decatur Application",
            "url": "https://example.com/adm.pdf",
            "source_page": "https://example.com/docket",
        },
        {
            "summary": "Specs",
            "url": "https://example.com/specs.docx",
            "source_page": "https://example.com/docket",
        },
    ]))

    entries = load_manifest(manifest_path)
    assert len(entries) == 2
    assert isinstance(entries[0], ManifestEntry)
    assert entries[0].summary == "ADM Decatur Application"
    assert entries[0].filename_from_url() == "adm.pdf"


def test_load_manifest_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path / "does_not_exist.json")


def test_load_manifest_rejects_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json at all")
    with pytest.raises(ValueError):
        load_manifest(bad)


def test_load_manifest_rejects_non_list_root(tmp_path):
    bad = tmp_path / "obj.json"
    bad.write_text('{"summary": "x", "url": "y"}')
    with pytest.raises(ValueError, match="must be a JSON list"):
        load_manifest(bad)


def test_load_manifest_rejects_entry_missing_url(tmp_path):
    bad = tmp_path / "no_url.json"
    bad.write_text(json.dumps([{"summary": "x"}]))
    with pytest.raises(ValueError, match="missing required 'url'"):
        load_manifest(bad)
