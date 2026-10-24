# Offline demo run (see scripts/demo.py). Pass --cpu to hide the GPU.
Set-Location (Join-Path $PSScriptRoot "..")
python scripts/demo.py @args
exit $LASTEXITCODE
