param([string]$PythonExe='python',[switch]$WithPlots)
$ErrorActionPreference='Stop'
$venv=Join-Path $PSScriptRoot '.venv'
& $PythonExe -c "import sys,tkinter; assert sys.version_info >= (3,12), 'Python 3.12+ with Tk is required'"
if($LASTEXITCODE -ne 0){throw 'Install Python 3.12+ with Tcl/Tk or pass -PythonExe.'}
if(-not(Test-Path -LiteralPath (Join-Path $venv 'Scripts/python.exe'))){
 & $PythonExe -m venv $venv
 if($LASTEXITCODE -ne 0){throw 'Virtual environment creation failed.'}
}
$python=Join-Path $venv 'Scripts/python.exe'
& $python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if($LASTEXITCODE -ne 0){throw 'Dependency installation failed.'}
& $python (Join-Path $PSScriptRoot 'pico-standalone/tools/desktop_control.py') --check-only
if($LASTEXITCODE -ne 0){throw 'Viewer validation failed.'}
Write-Host 'Ready: Start.cmd opens the viewer. See docs/SETUP_WINDOWS_EN.md. Firmware installation is separate.'
