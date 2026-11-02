@echo off
where code >nul 2>nul
if errorlevel 1 (
  start "" "%~dp0"
) else (
  call code "%~dp0"
)
