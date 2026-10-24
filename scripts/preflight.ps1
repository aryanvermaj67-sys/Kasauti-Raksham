# Demo-day preflight (see scripts/preflight.py): prints GO or NO-GO.
Set-Location (Join-Path $PSScriptRoot "..")
python scripts/preflight.py @args
exit $LASTEXITCODE
