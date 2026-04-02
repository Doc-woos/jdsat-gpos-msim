param(
    [string]$DocsDir = "docs",
    [int]$PngWidth = 2400,
    [double]$PngScale = 2,
    [string]$BackgroundColor = "white"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$docsPath = Join-Path $repoRoot $DocsDir
$mermaidCli = Join-Path $repoRoot "node_modules\.bin\mmdc.cmd"

if (-not (Test-Path $docsPath)) {
    throw "Docs directory not found: $docsPath"
}

if (-not (Test-Path $mermaidCli)) {
    throw "Mermaid CLI not found at $mermaidCli. Run 'npm install' first."
}

$mmdFiles = Get-ChildItem -Path $docsPath -Filter *.mmd | Sort-Object Name
if (-not $mmdFiles) {
    Write-Host "No .mmd files found under $docsPath"
    exit 0
}

foreach ($file in $mmdFiles) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $svgPath = Join-Path $docsPath ("{0}.svg" -f $baseName)
    $pngPath = Join-Path $docsPath ("{0}.png" -f $baseName)

    Write-Host "Rendering $($file.Name) -> $([System.IO.Path]::GetFileName($svgPath)), $([System.IO.Path]::GetFileName($pngPath))"

    & $mermaidCli -i $file.FullName -o $svgPath -b $BackgroundColor
    if ($LASTEXITCODE -ne 0) {
        throw "SVG render failed for $($file.Name)"
    }

    & $mermaidCli -i $file.FullName -o $pngPath -b $BackgroundColor -w $PngWidth -s $PngScale
    if ($LASTEXITCODE -ne 0) {
        throw "PNG render failed for $($file.Name)"
    }
}

Write-Host "Rendered $($mmdFiles.Count) Mermaid diagram(s)."
