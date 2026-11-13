param([string]$PythonExe='python',[switch]$WithPlots)
$ErrorActionPreference='Stop'
$venv=Join-Path $PSScriptRoot '.venv'
& $PythonExe -c "import sys,tkinter; assert sys.version_info >= (3,12), 'Python 3.12+ with Tk is required'"
if($LASTEXITCODE -ne 0){throw 'Install Python 3.12+ with Tcl/Tk or pass -PythonExe with its full path.'}
if(-not (Test-Path -LiteralPath (Join-Path $venv 'Scripts/python.exe'))){
    & $PythonExe -m venv $venv
    if($LASTEXITCODE -ne 0){throw 'Virtual environment creation failed.'}
}
$python=Join-Path $venv 'Scripts/python.exe'
& $python -m pip install -r (Join-Path $PSScriptRoot 'SEN0325-Pico-Setup/requirements.txt')
if($LASTEXITCODE -ne 0){throw 'Dependency installation failed.'}
if($WithPlots){
    & $python -m pip install -r (Join-Path $PSScriptRoot 'tests/requirements-plots.txt')
    if($LASTEXITCODE -ne 0){throw 'Plot dependency installation failed.'}
}
& $python (Join-Path $PSScriptRoot 'SEN0325-Pico-Setup/refresh_and_start.py') --check-only
if($LASTEXITCODE -ne 0){throw 'Source validation failed.'}
Write-Host 'Ready. See docs/SETUP_WINDOWS.md for Pico USB/driver and picotool setup.'
