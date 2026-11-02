@echo off
setlocal
set "PYTHONW=C:\Tools\Embedded\venv\Scripts\pythonw.exe"
if not exist "%PYTHONW%" (
  echo Missing Python runtime: %PYTHONW%
  pause
  exit /b 1
)
start "" "%PYTHONW%" "%~dp0SEN0325-Pico-Setup\sen0325_launcher.py" --profile coded-16-18
exit /b 0
