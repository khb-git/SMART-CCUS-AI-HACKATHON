# Docket scraper

Scrapes EPA Class VI docket pages for downloadable permit files and emits
a JSON manifest the RAG pipeline can consume.

## What it does

Given one or more docket page URLs, the scraper:

1. Fetches each page.
2. Finds every link to a downloadable file (`.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`).
3. Extracts the surrounding summary text (the descriptive paragraph or list item containing the link).
4. Writes a flat JSON list of `{summary, url, source_page}` entries.

The output is the input contract for `rag/manifest.py::load_manifest()`,
which the RAG ingestion pipeline calls to know which files to download
and ingest.

## Quick start

## End-to-end scraper pipeline

The scraper workflow now has two steps:

1. Scrape EPA docket pages and create a manifest.
2. Download the files listed in the manifest.

A config-driven workflow is available through the scripts in `scripts/`.

### Windows PowerShell

```powershell
.\scripts\run_scraper_pipeline.ps1

```bash
# Install the two deps (in addition to whatever's already in requirements.txt)
pip install requests beautifulsoup4

# Scrape one docket page
python scraper.py https://www.epa.gov/uic/some-docket-page

# Scrape multiple pages
python scraper.py page1_url page2_url page3_url -o data/manifest.json

# Or use a file with one URL per line
python scraper.py --urls-file docket_urls.txt -o data/manifest.json
```

Default output path is `data/manifest.json`.

## Output shape

```json
[
  {
    "summary": "ADM CCS2 Application Narrative — describes proposed injection well and CO2 sequestration plan",
    "url": "https://www.epa.gov/sites/default/files/2024-01/adm-ccs2-narrative.pdf",
    "source_page": "https://www.epa.gov/uic/adm-ccs2-permit-documents"
  },
  ...
]
```

Three fields per entry, all strings. `summary` is the descriptive text
from the page. `url` is always an absolute URL (the scraper resolves
relative hrefs against the source page). `source_page` is preserved so
the manifest can be filtered or grouped by docket later.

## How it plugs into the RAG scaffold

```
rag/manifest.py::load_manifest(path)
    -> list[ManifestEntry]
       each entry has .summary, .url, .source_page, and (after download) .local_path

rag/manifest.py::download_manifest(path, dest_dir)
    -> same, but downloads files first and populates .local_path

rag/pipeline.py::IngestionPipeline.ingest_permit(local_path, project_name)
    -> the existing pipeline takes it from there
```

The scraper is deliberately decoupled from the RAG pipeline — it
produces a manifest; the pipeline consumes it. That means scraping can
run on a different schedule from ingestion, and the same manifest can
be re-used to re-ingest after schema changes.

## Politeness

The scraper waits 1 second between requests by default (configurable
via `--delay`). EPA's site is public, but we still don't want to hammer
it. The User-Agent identifies us as a research scraper.

## Tests

```bash
pytest tests/
```

18 tests cover URL classification, summary extraction, end-to-end manifest
writing (with mocked HTTP — no real network calls in tests), and the
manifest loader's validation.

## When the summaries look bad

Different docket pages structure their HTML differently. The
`extract_summary` heuristic in `scraper.py` works on EPA's common patterns,
but if you find a docket where summaries come out as just the link text
or include too much noise, the fix is to add a per-page rule rather than
trying to make the universal heuristic smarter.

## TODOs

- `download_manifest` is a stub. Implementation sketch is in the
  docstring — pick it up when you're ready to wire the manifest into
  the ingestion pipeline.
- No retry logic on transient failures. Add `tenacity` when scraping
  starts hitting real flakiness.
- No JS rendering. If a future docket page loads files via JavaScript,
  swap `requests` for `playwright`.
