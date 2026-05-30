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
$delay = $config.delay_seconds
$timeout = $config.timeout_seconds
$retries = $config.retries
$backoff = $config.backoff_factor

Write-Host "Running scraper..."
python scraper.py `
    --urls-file $urlsFile `
    --output $manifestPath `
    --delay $delay `
    --timeout $timeout `
    --retries $retries `
    --backoff $backoff

Write-Host "Downloading files from manifest..."
python -c "from rag.manifest import download_manifest; download_manifest(r'$manifestPath', r'$downloadDir', delay=$delay, timeout=$timeout, retries=$retries, backoff_factor=$backoff)"

Write-Host "Scraper pipeline complete."
Write-Host "Manifest: $manifestPath"
Write-Host "Downloaded files: $downloadDir"