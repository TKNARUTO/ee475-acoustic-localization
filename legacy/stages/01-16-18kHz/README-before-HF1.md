# Tagalong | Acoustic Localization Prototype

**EE475 · Weekly milestone: 17 October 2026 · Desktop application v0.7 · Pico firmware v0.5**

This repository contains the acoustic sensing subsystem for the Tagalong following robot. A phone plays a known coded beacon; a DFRobot SEN0325 6+1 microphone array and Raspberry Pi Pico acquire synchronous audio; a Windows application detects the beacon and estimates its planar direction on a radar-style display.

The current milestone is an **audible-beacon bench prototype**. The computer performs direction estimation. The ESP32, forward-facing distance radar and vehicle controller are future integration work. The display reports bearing; its rings do not measure distance.

## Quick start on the configured Windows computer

1. Keep the existing SEN0325-to-Pico wiring. Connect one Pico by USB and close other serial monitors.
2. Double-click **`Start-Localizer.cmd`** in this folder. The interface is in English. If an earlier window is already open, close it and launch again to load the English interface.
3. If prompted for firmware, hold **BOOTSEL** while reconnecting USB. Release when **RPI-RP2** appears. The launcher validates and loads the supplied RAM-only diagnostic image.
4. Leave **Audible beacon** selected. Play `audio/phone/audible_beacon_right.wav` on the phone in a loop, then select **Start Radar**. Keep computer playback off during a phone test.
5. Once a stable arrow appears, select **Set Front** with the phone physically in front of the array. Keep the array fixed and move the phone left and right to check orientation.
6. Use **Stop Radar** to stop acquisition and **Stop Sound** to stop computer playback. Closing the application releases its serial connection.

Radar and computer playback are independent and both start off. The high-frequency option remains experimental and is not the demonstration baseline. RAM firmware disappears when power is removed and must then be loaded again.

## SEN0325-to-Pico GPIO wiring

The table below matches the current firmware pin assignments. **GPIO numbers and physical pin numbers are different**: for example, GP6 is physical pin 9.

| SEN0325 pin label | Pico signal / GPIO | Pico physical pin | Function |
| --- | --- | --- | --- |
| VIN | 3V3 OUT | 36 | 3.3 V supply for the current microphone test |
| GND | GND | 13 | Common ground |
| MIC_D0 | GP6 | 9 | Microphone data line 0, array → Pico |
| MIC_D1 | GP7 | 10 | Microphone data line 1, array → Pico |
| MIC_D2 | GP8 | 11 | Microphone data line 2, array → Pico |
| MIC_D3 | GP9 | 12 | Microphone data line 3, array → Pico |
| MIC_CK | GP10 | 14 | I2S bit clock (BCLK), Pico → array |
| MIC_WS | GP11 | 15 | I2S word select (WS/LRCLK), Pico → array |
| LED_CK | GP12 | 16 | LED clock, Pico → array |
| LED_DA | GP13 | 17 | LED data, Pico → array |

**Pico orientation:** with the USB connector at the top and the component side facing you, the left row runs from GP0 to GP15; the right row runs from VBUS down to GP16. The back-side photograph reverses left and right. Follow the GPIO names and physical pin numbers rather than the breadboard row numbers.

**SEN0325 connector orientation:** viewed from the side carrying the connector and its printed labels, as in the supplied photograph:

```text
Left      Right
LED_DA    LED_CK
MIC_D1    MIC_D0
MIC_D3    MIC_D2
MIC_CK    MIC_WS
GND       VIN
```

Disconnect USB before changing wires. Keep the current 3.3 V supply and ring LEDs off; do not confuse **3V3 OUT (pin 36)** with **3V3_EN (pin 37)** or VBUS. See [hardware and wiring notes](docs/HARDWARE.md) for the board-revision and power-supply details.

## Project contents

| Location | Contents |
| --- | --- |
| `SEN0325-Pico-Setup/` | Active integrated Pico SDK and desktop application workspace; existing launch/build paths are preserved. |
| `audio/phone/` | English-named, ready-to-transfer phone WAV files and playback notes. |
| `docs/` | User guide, hardware wiring, architecture, validation summary and bilingual weekly updates. |
| `reports/validation/` | Selected original machine-readable test evidence. |
| `tests/` | Repeatable signal-model, control and English-interface checks. |
| `references/` | Original proposal, project notes, datasheets, schematic and hardware photographs. |
| `releases/` | Distributable weekly source/documentation package and earlier release packages. |
| `archive/` | Historical development snapshots, Chinese instructions, migration records and pre-packaging backup. |
| `FILE_INDEX.txt` | Searchable list of current files and locations; generated without following directory junctions. |

The integrated workspace intentionally retains its current source layout for this milestone. Firmware source (`main.c`, `sen0325_i2s.pio`, `tone_filter.h`) and host Python modules live together there; validated binaries are in its `firmware/` folder. Shared compilers, SDKs and Python are installed outside this repository under `C:/Tools/Embedded` and are not bundled in the release. Legacy Chinese launcher filenames remain as compatibility entry points.

## What works at this milestone

- Seven synchronous microphone channels captured at 48 kHz using RP2040 PIO and DMA.
- USB raw audio bursts with packet length, sequence and CRC32 validation, plus dropped-block and RX-stall reporting.
- Known-code detection within the selected frequency band; audible direction estimation using multiple microphone pairs and SRP-PHAT.
- Radar-style 360° bearing display, front-reference calibration, mirror view, channel diagnostics and distance-tagged trial logging.
- Independent sound/radar controls and transferable phone audio.
- Faster acquisition scheduling and smooth display updates. A controlled live timing comparison improved the median capture/detection-loop rate from **2.92 to 4.57 Hz**. The UI timer targets approximately **30 frames/s**; these are different rates.

These features do not establish absolute angular accuracy, reliable operation beyond 1 m, measured distance, or completed autonomous following. See [validation and limitations](docs/VALIDATION.md).

## Development environment

The configured machine uses Python 3.12.4, Tk 8.6, NumPy 2.5.4, pyserial 3.5, Pico SDK 2.3.1, Arm GCC 14.2.1, CMake/Ninja and picotool 2.3.1. Dependency pins are recorded in `SEN0325-Pico-Setup/requirements.txt`.

From PowerShell in this project folder:

```powershell
# Run the desktop application with console output.
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\SEN0325-Pico-Setup\sen0325_launcher.py'

# Build the default RAM-only Pico image. This does not automatically flash a board.
& '.\SEN0325-Pico-Setup\Build.ps1'

# Validate the supplied binary without touching hardware.
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\SEN0325-Pico-Setup\verify_ram.py' '.\SEN0325-Pico-Setup\firmware\sen0325_setup-RAM.uf2'

# Repeat the offline signal-model and independent-control checks.
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\tests\verify_beacon_model.py'
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\tests\verify_controls.py'
```

On another Windows computer, create a Python 3.12 environment with Tk and install the pinned requirements. The launcher and build scripts currently contain local tool paths; update those paths before use. Building also requires the Pico SDK/toolchain and an ASCII build path. The existing machine uses `C:/Dev/Embedded/SEN0325-Pico-Setup`, a junction to the active workspace. The release is source plus assets, not a standalone installer.

## Documentation

- [User guide](docs/USER_GUIDE.md)
- [Wiring and hardware notes](docs/HARDWARE.md)
- [Signal pipeline and code map](docs/ARCHITECTURE.md)
- [Validation evidence and known limits](docs/VALIDATION.md)
- [Weekly update — English](docs/WEEKLY_UPDATE_EN.md)
- [周报 — 中文](docs/WEEKLY_UPDATE_ZH.md)
- [Bilingual weekly update](docs/WEEKLY_UPDATE_BILINGUAL.md)

## Next milestone

Measure bearing error at known angles and distances with the Samsung S25 Ultra, assess reverberation and rejection of unrelated audio, and calibrate geometry/orientation. Then define the Pico/ESP32 bearing-and-validity interface and integrate the distance radar and vehicle controller. Inaudible operation remains a separate experiment.
