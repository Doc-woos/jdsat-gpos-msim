param(
    [string]$GamePlanRepo = "C:\dev\jdsat-gameplan-os",
    [switch]$RenderDocs
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptRoot

powershell -ExecutionPolicy Bypass -File (Join-Path $scriptRoot "install_gameplan_editable.ps1") -GamePlanRepo $GamePlanRepo

if ($RenderDocs) {
    Push-Location $repoRoot
    try {
        npm install
        npm run docs:render-diagrams
    }
    finally {
        Pop-Location
    }
}
