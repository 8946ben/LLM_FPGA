param([string]$PythonExe = $env:PYTHON)

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
Push-Location $referenceDir
try {
    & $PythonExe -m unittest discover -p 'test_*.py' -v
    if ($LASTEXITCODE -ne 0) {
        throw "Reference tests failed with exit code $LASTEXITCODE"
    }
    & $PythonExe validate_source_contract.py
    if ($LASTEXITCODE -ne 0) {
        throw "Source contract validation failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
