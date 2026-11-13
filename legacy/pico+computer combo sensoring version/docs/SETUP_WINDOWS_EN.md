# Windows setup

Install Python 3.12+ with Tcl/Tk. From this template root:
```powershell
powershell -ExecutionPolicy Bypass -File .\Setup-Windows.ps1 -PythonExe 'C:\Path\To\Python312\python.exe'
```
Setup creates `.venv`, installs the pinned `SEN0325-Pico-Setup/requirements.txt` and checks Python sources. `-WithPlots` adds optional plot dependencies. Network access may be needed for installation.

Use the local `.venv` on a new PC. The unchanged launcher also supports `EE475_PYTHON` and the original maintainer runtime fallback; that fallback is not a portable requirement. `Update.cmd` validates/restarts local source only.

Connect a USB data cable. Hold BOOTSEL while connecting when another firmware is running. The launcher copies the validated SRAM-only v0.6 image through RPI-RP2; no picotool is needed for drive loading. RAM contents disappear after power loss. Optional picotool fallback can use `EE475_PICOTOOL`. Original Build/Load/Monitor helpers are owner-specific references and are not needed for normal use. The nearby v0.8 C source does not reproduce v0.6 by assertion.

```powershell
.\.venv\Scripts\python.exe .\tools\verify_handoff.py --output-dir C:\Path\To\ComboChecks
```
Keep check output outside this template. Hardware tests need exclusive serial access. No new PC driver installation or environment setup was performed by this documentation revision.

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](../PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
