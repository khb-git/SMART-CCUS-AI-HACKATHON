import json

from rag.manifest import download_manifest, load_manifest


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
    assert entries[0].local_path.endswith("permit.pdf")

    downloaded_file = download_dir / "permit.pdf"
    assert downloaded_file.exists()
    assert downloaded_file.read_bytes() == b"fake pdf bytes"


def test_download_manifest_skips_existing_files(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    existing_file = download_dir / "permit.pdf"
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