import json

from rag.manifest import download_manifest, load_manifest

from pathlib import Path


def test_load_manifest_accepts_local_path(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps([
            {
                "summary": "Permit file",
                "url": "https://example.com/files/permit.pdf",
                "source_page": "https://example.com/docket",
                "local_path": "data/raw_docs/permit.pdf",
            }
        ]),
        encoding="utf-8",
    )

    entries = load_manifest(manifest_path)

    assert len(entries) == 1
    assert entries[0].summary == "Permit file"
    assert entries[0].local_path == "data/raw_docs/permit.pdf"


def test_download_manifest_downloads_files(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    download_dir = tmp_path / "downloads"

    manifest_path.write_text(
        json.dumps([
            {
                "summary": "Permit file",
                "url": "https://example.com/files/permit.pdf",
                "source_page": "https://example.com/docket",
            }
        ]),
        encoding="utf-8",
    )

    class FakeResponse:
        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield b"fake pdf bytes"

    class FakeSession:
        def __init__(self):
            self.headers = {}

        def mount(self, prefix, adapter):
            pass

        def get(self, url, stream=False, timeout=None):
            return FakeResponse()

    import rag.manifest as manifest_module

    monkeypatch.setattr(manifest_module.requests, "Session", FakeSession)

    entries = download_manifest(
        manifest_path=manifest_path,
        dest_dir=download_dir,
        delay=0,
    )

    assert len(entries) == 1
    assert entries[0].local_path.endswith(".pdf")
    assert "permit__" in entries[0].local_path

    downloaded_file = Path(entries[0].local_path)
    assert downloaded_file.exists()
    assert downloaded_file.read_bytes() == b"fake pdf bytes"


def test_download_manifest_skips_existing_files(tmp_path, monkeypatch):
    from rag.manifest import ManifestEntry

    manifest_path = tmp_path / "manifest.json"
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    entry = ManifestEntry(
        summary="Permit file",
        url="https://example.com/files/permit.pdf",
        source_page="https://example.com/docket",
    )

    existing_file = download_dir / entry.filename_from_url()
    existing_file.write_bytes(b"already here")

    manifest_path.write_text(
        json.dumps([
            {
                "summary": "Permit file",
                "url": "https://example.com/files/permit.pdf",
                "source_page": "https://example.com/docket",
            }
        ]),
        encoding="utf-8",
    )

    class FakeSession:
        def __init__(self):
            self.headers = {}

        def mount(self, prefix, adapter):
            pass

        def get(self, url, stream=False, timeout=None):
            raise AssertionError("Should not download existing file")

    import rag.manifest as manifest_module

    monkeypatch.setattr(manifest_module.requests, "Session", FakeSession)

    entries = download_manifest(
        manifest_path=manifest_path,
        dest_dir=download_dir,
        delay=0,
    )

    assert entries[0].local_path == str(existing_file)
    assert existing_file.read_bytes() == b"already here"

def test_filename_from_url_adds_stable_hash():
    from rag.manifest import ManifestEntry

    entry = ManifestEntry(
        summary="Test",
        url="https://epa.gov/files/sequestration.pdf",
        source_page="https://epa.gov/page-a",
    )

    filename = entry.filename_from_url()

    assert filename.startswith("sequestration__")
    assert filename.endswith(".pdf")
    assert len(filename.split("__")[1].replace(".pdf", "")) == 12


def test_filename_from_url_avoids_same_basename_collision():
    from rag.manifest import ManifestEntry

    first = ManifestEntry(
        summary="First",
        url="https://epa.gov/files/project-a/sequestration.pdf",
        source_page="https://epa.gov/page-a",
    )
    second = ManifestEntry(
        summary="Second",
        url="https://epa.gov/files/project-b/sequestration.pdf",
        source_page="https://epa.gov/page-b",
    )

    assert first.filename_from_url() != second.filename_from_url()
    assert first.filename_from_url().startswith("sequestration__")
    assert second.filename_from_url().startswith("sequestration__")


def test_download_manifest_writes_local_path_back_to_manifest(tmp_path, monkeypatch):
    import json
    import rag.manifest as manifest_module
    from rag.manifest import download_manifest

    manifest_path = tmp_path / "manifest.json"
    download_dir = tmp_path / "downloads"

    manifest_path.write_text(
        json.dumps([
            {
                "summary": "Permit file",
                "url": "https://example.com/project-a/sequestration.pdf",
                "source_page": "https://example.com/docket",
            }
        ]),
        encoding="utf-8",
    )

    class FakeResponse:
        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield b"fake pdf bytes"

    class FakeSession:
        def __init__(self):
            self.headers = {}

        def mount(self, prefix, adapter):
            pass

        def get(self, url, stream=False, timeout=None):
            return FakeResponse()

    monkeypatch.setattr(manifest_module.requests, "Session", FakeSession)

    entries = download_manifest(
        manifest_path=manifest_path,
        dest_dir=download_dir,
        delay=0,
    )

    updated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert len(entries) == 1
    assert updated_manifest[0]["local_path"] == entries[0].local_path
    assert updated_manifest[0]["local_path"].endswith(".pdf")
    assert "sequestration__" in updated_manifest[0]["local_path"]