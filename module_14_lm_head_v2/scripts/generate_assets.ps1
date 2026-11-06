param(
    [Parameter(Mandatory = $true)][string]$ModelPath,
    [Parameter(Mandatory = $true)][string]$FixtureRoot,
    [Parameter(Mandatory = $true)][string]$OutputRoot,
    [string]$PythonExe = $env:PYTHON,
    [switch]$SkipGolden
)

$ErrorActionPreference = 'Stop'
if (-not $PythonExe) {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command) {
        $PythonExe = $command.Source
    }
}
if (-not $PythonExe -or -not (Test-Path -LiteralPath $PythonExe)) {
    throw 'Python was not found. Pass -PythonExe or set the PYTHON environment variable.'
}

$referenceDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'reference'
$arguments = @(
    (Join-Path $referenceDir 'export_bf16_assets.py'),
    '--model', $ModelPath,
    '--fixture-root', $FixtureRoot,
    '--output-root', $OutputRoot
)
if ($SkipGolden) {
    $arguments += '--skip-golden'
}
& $PythonExe @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Asset generation failed with exit code $LASTEXITCODE"
}
