#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-config/scraper_config.example.json}"

if [ ! -f "$CONFIG_PATH" ]; then
  echo "Config file not found: $CONFIG_PATH" >&2
  exit 1
fi

read_json() {
  python -c "import json; print(json.load(open('$CONFIG_PATH'))['$1'])"
}

URLS_FILE="$(read_json urls_file)"
MANIFEST_PATH="$(read_json manifest_path)"
DOWNLOAD_DIR="$(read_json download_dir)"
DELAY="$(read_json delay_seconds)"
TIMEOUT="$(read_json timeout_seconds)"
RETRIES="$(read_json retries)"
BACKOFF="$(read_json backoff_factor)"

echo "Running scraper..."
python scraper.py \
  --urls-file "$URLS_FILE" \
  --output "$MANIFEST_PATH" \
  --delay "$DELAY" \
  --timeout "$TIMEOUT" \
  --retries "$RETRIES" \
  --backoff "$BACKOFF"

echo "Downloading files from manifest..."
python -c "from rag.manifest import download_manifest; download_manifest('$MANIFEST_PATH', '$DOWNLOAD_DIR', delay=float('$DELAY'), timeout=int('$TIMEOUT'), retries=int('$RETRIES'), backoff_factor=float('$BACKOFF'))"

echo "Scraper pipeline complete."
echo "Manifest: $MANIFEST_PATH"
echo "Downloaded files: $DOWNLOAD_DIR"
