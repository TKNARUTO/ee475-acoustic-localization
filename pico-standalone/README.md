# Pico standalone acoustic localization

SEN0325 audio is captured and processed on Raspberry Pi Pico; ESP32 receives bearing/status packets. The PC is an optional monitor. Current stage: **v0.2-link_diag communication validation**; further FFT and dual-core optimization is paused.

| Document | English | 中文 |
|---|---|---|
| Setup, exact tools and status | [README_EN](README_EN.md) | [README_ZH](README_ZH.md) |
| Communication decisions and evidence | [Communication notebook](COMMUNICATION_NOTEBOOK_EN.md) | [通信笔记](COMMUNICATION_NOTEBOOK_ZH.md) |
| Algorithm, resources and bandwidth | [Design notebook](DESIGN_NOTEBOOK_EN.md) | [设计笔记](DESIGN_NOTEBOOK_ZH.md) |

Pico uses **native C/C++ with Pico SDK 2.3.1**, not an Arduino sketch. ESP32 uses **NodeMCU-32S / classic ESP32**, Arduino IDE 2.3.8, CLI 1.4.1 and Espressif board package 3.3.12; it is not ESP32-S3.

Both communication firmwares have been written and verified. Background, software-reboot and no-Pico-USB-reader observations are documented; physical cold-start and known-angle acoustic validation are separate checks. The **0.2–0.5 s delay target remains unmet**; diagnostic angles are not valid motor targets.
