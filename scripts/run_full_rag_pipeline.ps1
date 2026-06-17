param(
    [string]$ConfigPath = "config/scraper_config.example.json"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ConfigPath)) {
    Write-Error "Config file not found: $ConfigPath"
}

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

$urlsFile = $config.urls_file
$manifestPath = $config.manifest_path
$downloadDir = $config.download_dir
$chunkedDir = $config.chunked_dir
$persistDirectory = $config.persist_directory

$delay = $config.delay_seconds
$timeout = $config.timeout_seconds
$retries = $config.retries
$backoff = $config.backoff_factor

# ----------------------------
# STEP 1: SCRAPE
# ----------------------------
Write-Host "Running scraper..."
python ./tools/scraper.py `
    --urls-file $urlsFile `
    --output $manifestPath `
    --delay $delay `
    --timeout $timeout `
    --retries $retries `
    --backoff $backoff

# ----------------------------
# STEP 2: DOWNLOAD FILES
# ----------------------------
Write-Host "Downloading files from manifest..."
python -c "from rag.manifest import download_manifest; download_manifest(r'$manifestPath', r'$downloadDir', delay=$delay, timeout=$timeout, retries=$retries, backoff_factor=$backoff)"

# ----------------------------
# STEP 3: CHUNK DOCUMENTS
# ----------------------------
Write-Host "Chunking documents..."
python -m ingestion.main `
    --manifest $manifestPath `
    --output $chunkedDir

# ----------------------------
# STEP 4: INDEX INTO CHROMA
# ----------------------------
Write-Host "Indexing chunks into Chroma..."
python -m rag.index_chunks `
    --chunked-dir $chunkedDir `
    --collection auto `
    --persist-directory $persistDirectory `
    --batch-size 32

# ----------------------------
# DONE
# ----------------------------
Write-Host ""
Write-Host "✅ RAG corpus build complete."
Write-Host "Manifest: $manifestPath"
Write-Host "Raw docs: $downloadDir"
Write-Host "Chunked docs: $chunkedDir"
Write-Host "Chroma DB: $persistDirectory"
