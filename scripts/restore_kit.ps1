# Restore a kit made by make_kit.ps1 onto this laptop, after checking every file against its manifest; then preflight.
# Usage: scripts\restore_kit.ps1 -Kit E:\kasauti_kit [-Repo <clone>] [-HomeDir <home>]   (defaults: this repo, $HOME)
param([Parameter(Mandatory)][string]$Kit, [string]$Repo = (Split-Path $PSScriptRoot -Parent), [string]$HomeDir = $HOME)
$ErrorActionPreference = "Stop"
$bad = 0
foreach ($line in Get-Content (Join-Path $Kit "MANIFEST.sha256")) {
  $sha, $rel = $line -split "  ", 2
  if ((Get-FileHash (Join-Path $Kit $rel) -Algorithm SHA256).Hash.ToLower() -ne $sha) { Write-Output "CHANGED: $rel"; $bad++ }
}
if ($bad) { throw "$bad file(s) in the kit do not match MANIFEST.sha256; not restoring" }
Write-Output "manifest OK: every file matches"
$ollama = if ($env:OLLAMA_MODELS) { $env:OLLAMA_MODELS } else { Join-Path $HomeDir ".ollama\models" }
$easyocr = Join-Path $HomeDir ".EasyOCR"
$dest = [ordered]@{ "repo" = $Repo; "ollama_models" = $ollama; "easyocr" = $easyocr }
foreach ($k in $dest.Keys) {
  robocopy (Join-Path $Kit $k) $dest[$k] /E /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "restore failed: $k (robocopy $LASTEXITCODE)" }
  Write-Output "restored $k -> $($dest[$k])"
}
$env:EASYOCR_MODULE_PATH = $easyocr
Write-Output "Restart Ollama so it sees the restored models, then:"
python (Join-Path $Repo "scripts\preflight.py")
