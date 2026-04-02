$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptRoot

Push-Location $repoRoot
try {
    Remove-Item Env:GAMEPLAN_SRC -ErrorAction SilentlyContinue
    python -m pytest tests -q
}
finally {
    Pop-Location
}
