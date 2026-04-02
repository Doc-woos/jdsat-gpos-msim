param(
    [string]$GamePlanRepo = "C:\dev\jdsat-gameplan-os"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $GamePlanRepo)) {
    throw "GamePlanOS repo not found at '$GamePlanRepo'."
}

python -m pip install -e $GamePlanRepo
