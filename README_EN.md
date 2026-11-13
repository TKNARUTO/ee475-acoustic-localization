# EE475 Acoustic Localization
**Release stage: standalone Pico + ESP32 communication, 12 November 2026**

The phone plays an HF2 gap beacon. SEN0325 provides raw microphone data. The **Pico now captures and computes direction locally** and sends compact results to ESP32. Windows only displays telemetry. ESP32 currently receives and acknowledges results; it does not run the acoustic estimator or drive motors.

**Stage result:** UART fields match between boards, persistent firmware has been verified, and communication continues without a PC client opening the Pico port. This is not yet a ready-to-follow robot: observed results still exceed the freshness limit, so all measured target-valid flags were zero. The 0.2–0.5 s goal remains open. See the [test report](reports/communication-2026-11-12/REPORT_EN.md).

## Platforms — choose the right board and package
| Component | Hardware / platform | Toolchain used | Board / port |
|---|---|---|---|
| Pico estimator | Raspberry Pi Pico, RP2040, C/C++ | Pico SDK **2.3.1**, Arm GNU **14.2.Rel1 / GCC 14.2.1**, CMake **4.4.4**, Ninja **1.13.2**, picotool **2.3.1** | SDK board **pico**; Windows currently **COM8**, previously COM5 |
| ESP32 receiver | 38-pin **NodeMCU ESP-32S**, classic ESP32-D0WD-V3, 4 MiB Flash | **Arduino IDE 2.3.8**, Arduino CLI **1.4.1**, **esp32 by Espressif Systems 3.3.12** | Arduino board **NodeMCU-32S**, FQBN **esp32:esp32:nodemcu-32s**; owner's port **COM6** |
| Optional viewer | Windows, Python + Tk | Python **3.12.4**, pyserial **3.5**; NumPy/Matplotlib for offline tests/plots | Auto-detects one Pico; does not own ESP32 port |
| Phone transmitter | Android 8+ / API 26+, Samsung S25 Ultra used by operator | Beacon Loop **1.2**, Java; compile/target API **35** | APK and source under android-player |

**NodeMCU-32S is the board selection, esp32 is the board package, and COM6 is a local serial port.** This board is not ESP32-S3. Do not select Arduino Nano ESP32 or ESP32S3 Dev Module. Different PCs/USB modes may assign different ports. Pico firmware uses the Pico SDK, not an Arduino sketch.

- [ESP32 Arduino installation, compile and upload](esp32-link/gap_receiver/README_EN.md)
- [Pico build, flash and numeric options](pico-standalone/README_EN.md)
- [Windows viewer setup](docs/SETUP_WINDOWS_EN.md)
- [Android playback/build](android-player/README_EN.md)

## Run the current system
1. With power removed, check the [full GPIO table](docs/HARDWARE_EN.md). Keep the existing array wiring.
2. Power each board by its own USB. Add only **Pico GP0/TX → ESP P16/RX**, **Pico GP1/RX ← ESP P17/TX**, and **GND ↔ GND**. No board-to-board power wire.
3. Install the listed firmware separately if needed. Root launchers do not flash anything.
4. Run **Start.cmd** to open/focus the optional monitor. **Update.cmd** checks local viewer code and restarts it; it does not download Git updates. Pico scans automatically. Closing the viewer leaves Pico running; Pause/Resume sends an explicit acquisition command.
5. On the phone install [BeaconLoop-1.2.apk](android-player/releases/BeaconLoop-1.2.apk). Select **Use HF2 gap beacon**, keep Normalize off, then Play. Or loop the [reference WAV](audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav) / [MP3](audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3).
6. For a repeatable test fix phone angle, distance and volume, then deliberately pause and resume. Record true physical angles before judging accuracy. Amber diagnostic fits are not fresh control commands.

The fixed waveform is **18–22 kHz**, 48 kHz sample rate, 4096 samples per period: 2048 sound + 2048 silence (42.67 ms each). The intentional silence is not a disconnect. The player can import other audio; the current standalone Pico cannot learn an arbitrary imported beacon. It must match the compiled reference. High-frequency audibility and range depend on the listener and hardware.

## Structure and ownership
| Folder | Role |
|---|---|
| pico-standalone/ | Active Pico source, fixed HF2 DSP, tests, release UF2, optional Windows viewer |
| esp32-link/gap_receiver/ | Separate Arduino sketch: UART receive/ACK, diagnostics and expiry; no motors |
| android-player/ | Java source, APK, bounded optional gain, local file import and looping |
| audio/phone/HF2-gap-test/ | Matched transmitter WAV/MP3 |
| docs/ | Bilingual setup, wiring, architecture and teammate/AI handoff |
| reports/communication-2026-11-12/ | Bilingual report, measured metrics and comparison figures |
| tools/ | Launch, catalog and publication verification helpers |
| references/ | Supplied hardware/project reference documents; not current firmware instructions |
| legacy/pico+computer combo sensoring version/ | Only retained legacy version: final Windows-DSP + Pico-capture template; matching ZIP adjacent |

The [file catalog](docs/FILE_CATALOG_EN.md) lists each shared file and purpose; [Chinese catalog](docs/FILE_CATALOG_ZH.md) is separate. Source code and interface text use English; human explanations use separate EN/ZH documents. Machine-readable manifests remain single files.

## Handoff and limitations
Read [team/AI handoff](docs/TEAM_HANDOFF_EN.md), [architecture and predicted integration bugs](docs/INTEGRATION_EN.md), [validation](docs/VALIDATION_EN.md), and [communication decision notebook](pico-standalone/COMMUNICATION_NOTEBOOK_EN.md). These notes record requirements, design decisions, tests and remaining work.

The old computer-processing baseline remains useful and has lower measured update intervals in earlier tests. Current processing is single-core on the Pico; FFT/dual-core optimization is paused while this communication stage is preserved. Do not remove freshness checks to make an amber arrow appear valid, or reject a direction solely for making a large turn. No distance estimator, motor controller, obstacle avoidance or autonomous following is delivered here.

Private microphone recordings, per-run logs, keys, toolchains and original board backups remain local. Removed historical versions were hash-verified into an external local archive before publication. Only shareable project files are synchronized to GitHub; see [sharing and release checks](docs/SHARING_EN.md).
