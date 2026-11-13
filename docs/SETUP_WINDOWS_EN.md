# Windows setup and exact entry points
Use Windows PowerShell. Install Python 3.12+ **with Tcl/Tk**, then from the project root:
```powershell
.\Setup-Windows.ps1 -PythonExe 'C:\Path\To\Python312\python.exe'
.\Start.cmd
```
The setup creates .venv, installs requirements.txt, and checks the standalone viewer. Existing installations can set EE475_PYTHON to their configured pythonw.exe. The owner's fallback runtime is a convenience, not a prerequisite on another computer. Update.cmd restarts local code only; use Git separately to get new source.

The two main user entries are Start.cmd and Update.cmd. Setup-Windows.ps1 is a one-time install helper. Neither launcher flashes a board or plays sound. Viewer logs are local under pico-standalone/logs; never commit them. It auto-detects one Pico with the standalone USB interface. Firmware v0.2-link_diag and integer_q15_fast should appear in telemetry.

Pico uses native Pico SDK 2.3.1, Arm GNU 14.2.Rel1 and picotool 2.3.1; see [its README](../pico-standalone/README_EN.md) for explicit integer FFT/FAST options and the persistent UF2. **Do not run the legacy launcher to connect the standalone firmware**: it loads a different capture image.

ESP32 uses Arduino IDE 2.3.8 / CLI1.4.1, **esp32 by Espressif Systems 3.3.12**, board **NodeMCU-32S**. Follow [ESP32 setup](../esp32-link/gap_receiver/README_EN.md). COM6 was observed for ESP and COM8 for Pico; re-enumerate with:
```powershell
python -m serial.tools.list_ports -v
arduino-cli board list
```
A generic USB Serial Port label can still be a valid ESP port. Select the board explicitly if automatic identification is unavailable. Close any serial monitor before another program opens that port. USB bootloader and normal firmware may enumerate differently.

Finite two-port capture (replace ports, use a fresh output directory outside this project):
```powershell
python pico-standalone/tools/monitor.py --port COM8 --port COM6 --seconds 30 --output C:\BenchResults\trial-new
python pico-standalone/tools/analyze_link_trial.py C:\BenchResults\trial-new --output C:\BenchResults\analysis-new
```
The monitor captures bounded startup raw bytes, resets each input buffer once, aligns at a newline, then starts the formal interval. It does not filter duplicated packets during that interval. It does not produce acoustic direction; Pico does.
