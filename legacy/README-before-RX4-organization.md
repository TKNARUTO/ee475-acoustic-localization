# Tagalong | Acoustic Localization Prototype

**EE475 · Current desktop checkpoint: RX3, 27 October 2026 · Pico firmware v0.6-RX2**

Current desktop status: [RX3 direction continuity README](stages/05-direction-diagnostics/README.md), [phase notes](stages/05-direction-diagnostics/PROGRESS_NOTES.md), [change details](stages/05-direction-diagnostics/CHANGE_DETAILS.md), and [phone continuity report](reports/direction-continuity-2026-10-27/DIRECTION_CONTINUITY_ZH.md). Code confirmation is separated from direction fitting, and short raw diagnostics save automatically. Identical-input phone replays show fewer confirmation waits; pair-delay inconsistency and physical accuracy remain unresolved.

Previous RX2 transport status: [latency reduction README](stages/04-latency-reduction/README.md), [progress notes](stages/04-latency-reduction/PROGRESS_NOTES.md), [change details](stages/04-latency-reduction/CHANGE_DETAILS.md), and [measured latency report](reports/latency-reduction-2026-10-27/LATENCY_REDUCTION_ZH.md). Firmware USB buffering and CRC computation reduce normal packet wait from about 208 ms to 164 ms in the live benchmark. The connected Pico and default RAM image are updated; v0.5 is upgraded automatically after validation. The [phone playback observation](reports/phone-observation-2026-10-27/README.md) records intermittent direction output despite code hits. Phone audio was interrupted during that test, so whole-session no-code counts are not a receiver failure rate. Physical direction stability, angular accuracy and range remain unresolved. Earlier [RX1 recovery](stages/03-packet-timing/README.md), [20 kHz receiver](stages/02-20kHz/README.md), and [original diagnosis](reports/delay-diagnosis-2026-10-22/DELAY_DIAGNOSIS_ZH.md) are retained.

A phone plays a coded beacon. A SEN0325 6+1 array and Raspberry Pi Pico capture synchronous audio, and this Windows receiver estimates bearing. The radar rings do not measure distance. ESP32, distance radar and motor integration remain future work.

## Quick start on the configured Windows computer

1. Keep the GPIO wiring below and connect one Pico. Close other serial monitors.
2. Open **Start-20kHz.cmd**. The standard Start-Localizer entry also now defaults to the 20 kHz receiver. Select **Start Scan**; computer playback is not implemented.
3. Loop **audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3** on the phone. The preset uses a 20 kHz center with 19–21 kHz bandwidth. Files 11–15 are pure level probes and do not produce a bearing.
4. Use **Import Beacon** for a compatible local MP3/WAV reference. The app analyzes and validates it before switching; play the same file on the phone. See the stage README for periodic-code restrictions.
5. The second panel shows actual spectrum and sampled waveform, even with no matching beacon. Code hits and valid direction are separate checks.
6. Set Front defines the physical forward reference after stable measurements. Advanced provides reconnect, mirror view, history and measured-distance trials. Completed 10 s trials save both metrics and local raw data for diagnosis.

7. Short raw diagnostic snapshots save automatically under `SEN0325-Pico-Setup/logs/direction-diagnostics/` when repeated fit failures or continuous valid bearings occur. See the RX3 README for limits and replay.

The original 17 October package and HF1 stage are retained as historical checkpoints. The earlier diagnosis recorded frequent geometric-fit rejection and rare packet-validation interruptions. The latest RX3 snapshots further identify mutually inconsistent pair-delay estimates, while confirmation waiting is reduced. Raising frequency does not establish better range or penetration.

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
| `audio/phone/` | Current phone MP3 pack, lossless reference WAVs and playback notes. |
| `docs/` | User guide, hardware wiring, architecture, validation summary and bilingual weekly updates. |
| `reports/validation/` | Selected original machine-readable test evidence. |
| `stages/05-direction-diagnostics/` | Current RX3 continuity fix, automatic raw snapshots, same-input replays, delay diagnosis and phase notes. |
| `stages/04-latency-reduction/` | Preserved RX2 USB/CRC speed improvement and firmware evidence. |
| `stages/03-packet-timing/` | Preserved RX1 packet recovery and host timing evidence. |
| `stages/02-20kHz/` | Earlier 20 kHz receiver, import/codec/UI and diagnostic checkpoint. |
| `stages/01-16-18kHz/` | Historical HF1 checkpoint, raw phone debugging data and pre-stage backup. |
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
- Receive-only scan controls, transferable phone MP3s and per-frequency received-level diagnostics.
- Experimental HF1 band-matched code detection, spectral interference weighting and bounded pair-delay localization.
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

# Repeat the offline signal-model and scanner-control checks.
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\tests\verify_beacon_model.py'
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\tests\verify_controls.py'
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\tests\verify_highband_stage1.py'
```

On another Windows computer, create a Python 3.12 environment with Tk and install the pinned requirements. The launcher and build scripts currently contain local tool paths; update those paths before use. Building also requires the Pico SDK/toolchain and an ASCII build path. The existing machine uses `C:/Dev/Embedded/SEN0325-Pico-Setup`, a junction to the active workspace. The release is source plus assets, not a standalone installer.

## Documentation

- [Current HF2 operation and limits](stages/02-20kHz/README.md)
- [Delay diagnosis](reports/delay-diagnosis-2026-10-22/DELAY_DIAGNOSIS_ZH.md)
- [Earlier user guide](docs/USER_GUIDE.md)
- [Wiring and hardware notes](docs/HARDWARE.md)
- [Signal pipeline and code map](docs/ARCHITECTURE.md)
- [Validation evidence and known limits](docs/VALIDATION.md)
- [Weekly update — English](docs/WEEKLY_UPDATE_EN.md)
- [周报 — 中文](docs/WEEKLY_UPDATE_ZH.md)
- [Bilingual weekly update](docs/WEEKLY_UPDATE_BILINGUAL.md)

## Next milestone

Measure bearing error at known angles and distances with the Samsung S25 Ultra, assess reverberation and rejection of unrelated audio, and calibrate geometry/orientation. Then define the Pico/ESP32 bearing-and-validity interface and integrate the distance radar and vehicle controller. Inaudible operation remains a separate experiment.
