# Platform and tool requirements

This archive runs the older **Windows + Pico capture** workflow. Windows computes direction. It is not the current independent Pico firmware.

| Purpose | Requirement / recorded version |
|---|---|
| Receiver | Windows 10/11; Python 3.12+ including Tcl/Tk |
| Python runtime | numpy 2.5.4; pyserial 3.5; imageio-ffmpeg 0.6.0, pinned in the retained requirements file |
| Capture board | Raspberry Pi Pico / RP2040; USB data cable; supplied v0.6-RX2 RAM UF2 |
| Phone | Beacon Loop 1.2, version code 3; Android API 26 minimum, API 35 target |
| Optional reset/loading tool | picotool 2.3.1 was observed on the maintainer computer; BOOTSEL drive loading does not require it |
| Development inventory, observed 12 November 2026 | Pico SDK 2.3.1; Arm GNU Toolchain 14.2.Rel1 / GCC 14.2.1; CMake 4.4.4; Ninja 1.13.2.git.kitware.jobserver-pipe-1 |

These tool versions describe the installed development environment, **not a proven reproduction toolchain for the shipped v0.6 binary**. The supplied adjacent C source is v0.8-BRIDGE. No exact matching v0.6 source snapshot was established. SDKs, Python, JDK/Android build tools and signing keys are not bundled. Install the pinned runtime packages using this template's Setup-Windows.ps1. The Android source is outside this compact archive.

The Pico RAM image disappears on power loss and must be loaded again. Windows version coverage, drivers on a new PC, S25 Ultra playback/permissions and physical accuracy require actual testing; the package checks do not establish these.
