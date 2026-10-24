# Copy everything a clone lacks into a kit folder (pen drive), write a SHA-256 manifest and print the size.
# Usage: scripts\make_kit.ps1 -Target E:\kasauti_kit
# The kit holds .env, which holds EVIDENCE_KEY: keep the drive with the team.
param([Parameter(Mandatory)][string]$Target)
$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$ollama = if ($env:OLLAMA_MODELS) { $env:OLLAMA_MODELS } else { Join-Path $HOME ".ollama\models" }
$easyocr = if ($env:EASYOCR_MODULE_PATH) { $env:EASYOCR_MODULE_PATH } else { Join-Path $HOME ".EasyOCR" }
$items = [ordered]@{
  "repo\models" = "$repo\models"; "repo\wheels" = "$repo\wheels"; "repo\data\media" = "$repo\data\media"
  "repo\data\footage_index" = "$repo\data\footage_index"; "repo\frontend\node_modules" = "$repo\frontend\node_modules"
  "ollama_models" = $ollama; "easyocr" = $easyocr
}
New-Item -ItemType Directory -Force $Target | Out-Null
foreach ($k in $items.Keys) {
  if (-not (Test-Path $items[$k])) { throw "missing: $($items[$k])" }
  robocopy $items[$k] (Join-Path $Target $k) /E /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "copy failed: $k (robocopy $LASTEXITCODE)" }
  Write-Output "copied $k"
}
Copy-Item "$repo\.env" (Join-Path $Target "repo\.env")
Write-Output "copied repo\.env"
$root = (Resolve-Path $Target).Path.TrimEnd("\") + "\"
$files = Get-ChildItem $Target -Recurse -File | Where-Object Name -ne "MANIFEST.sha256" | Sort-Object FullName
$lines = foreach ($f in $files) { "{0}  {1}" -f (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower(), $f.FullName.Substring($root.Length).Replace("\", "/") }
[IO.File]::WriteAllLines((Join-Path $Target "MANIFEST.sha256"), [string[]]$lines)
$gb = ($files | Measure-Object Length -Sum).Sum / 1GB
Write-Output ("kit: {0} files, {1:N2} GB, manifest {2}" -f $files.Count, $gb, (Join-Path $Target "MANIFEST.sha256"))
