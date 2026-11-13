@echo off
setlocal
set "EE475_RUNTIME=%EE475_PYTHON%"
if not defined EE475_RUNTIME set "EE475_RUNTIME=%~dp0..\.venv\Scripts\pythonw.exe"
if not exist "%EE475_RUNTIME%" set "EE475_RUNTIME=C:\Tools\Embedded\venv\Scripts\pythonw.exe"
if not exist "%EE475_RUNTIME%" (
  echo Run Setup-Windows.ps1 or set EE475_PYTHON to a configured Python executable.
  pause
  exit /b 1
)
start "" "%EE475_RUNTIME%" "%~dp0..\SEN0325-Pico-Setup\refresh_and_start.py" %*
exit /b 0
