# EE475 Acoustic Localization

[Full English guide](README_EN.md) · [中文说明](README_ZH.md)

**Current stage:** SEN0325 → Pico standalone estimation → ESP32 UART reception. Windows is an optional radar/timing monitor; the phone plays the fixed HF2 gap beacon.

| Component | Platform and tested setup |
|---|---|
| Pico | Raspberry Pi Pico / RP2040; native C/C++, **Pico SDK 2.3.1**, Arm GNU 14.2.Rel1, CMake 4.4.4 |
| ESP32 | **38-pin NodeMCU ESP-32S**, classic ESP32; **Arduino IDE 2.3.8 / CLI 1.4.1** |
| Arduino board package | **esp32 by Espressif Systems 3.3.12** |
| Arduino board selection | **NodeMCU-32S**; FQBN **esp32:esp32:nodemcu-32s** — not ESP32-S3 |
| Observed USB ports | ESP32 **COM6**, Pico **COM8**; select the actual port on your computer |
| Windows / Android | Python 3.12 + Tk; Beacon Loop 1.2, Android API26+ |

The board package, board type and COM port are different settings. Pico is a Pico SDK project; ESP32 is an Arduino sketch. [ESP32 installation/build/upload](esp32-link/gap_receiver/README_EN.md) · [Pico setup](pico-standalone/README_EN.md) · [GPIO wiring](docs/HARDWARE_EN.md).

**Status:** communication fields match in clean trials, software reboot recovers, and the link continues without a Pico PC client. Fresh control targets and the **0.2–0.5 s delay goal remain unmet**; no motor commands are included. Read the [English report](reports/communication-2026-11-12/REPORT_EN.md) / [中文报告](reports/communication-2026-11-12/REPORT_ZH.md).

Use **Start.cmd** and **Update.cmd** for the optional viewer. Separate folders contain Pico firmware, ESP32 Arduino source and the Android player. The only legacy template is [the final Pico + computer version](legacy/pico+computer%20combo%20sensoring%20version/README.md).

[File catalog](docs/FILE_CATALOG_EN.md) · [Team and AI handoff](docs/TEAM_HANDOFF_EN.md) · [Architecture and integration risks](docs/INTEGRATION_EN.md)
