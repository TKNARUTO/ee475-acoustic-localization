@echo off
setlocal
set "PYTHONW=%EE475_PYTHON%"
if not defined PYTHONW set "PYTHONW=%~dp0.venv\Scripts\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=C:\Tools\Embedded\venv\Scripts\pythonw.exe"
if not exist "%PYTHONW%" (
  echo Run Setup-Windows.ps1 first, or set EE475_PYTHON to a configured Python executable.
  pause
  exit /b 1
)
start "" "%PYTHONW%" "%~dp0SEN0325-Pico-Setup\refresh_and_start.py"
exit /b 0
