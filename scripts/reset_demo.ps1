# Reset the demo to its seed state (see scripts/reset_demo.py).
Set-Location (Join-Path $PSScriptRoot "..")
python scripts/reset_demo.py @args
exit $LASTEXITCODE
