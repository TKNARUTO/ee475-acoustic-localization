# Pico–ESP32 communication

Updated 12 November 2026. [中文](README_ZH.md)

The current path is **phone sound → SEN0325 → Pico standalone → ESP32 receive/ACK**. Pico captures the microphones and computes the HF2 Gap bearing. The computer is an optional monitor. ESP32 receives compact results and returns acknowledgments; motor control and range sensing remain separate integration work.

Start with [gap_receiver/README_EN.md](gap_receiver/README_EN.md) for Arduino installation, wiring, upload and protocol details. `gap_receiver/` is the current source. The earlier low-frequency ESP32 examples are retired from this handoff.

| Item | Current configuration |
|---|---|
| Hardware | NodeMCU ESP-32S, classic ESP32 |
| IDE / CLI | Arduino IDE **2.3.8** / Arduino CLI **1.4.1** |
| Board Manager package | **esp32 by Espressif Systems 3.3.12** |
| Board / FQBN | **NodeMCU-32S** / `esp32:esp32:nodemcu-32s` |
| Stable package index | `https://espressif.github.io/arduino-esp32/package_esp32_index.json` |
| UART | 115200, 8N1; ESP32 RX16 and TX17 |
| Port | Local example: ESP32 COM6, Pico COM8. Discover the actual ports on each computer. |

The **package**, **board model**, and **COM port** are three different selections. This tested board is not ESP32-S3 or Arduino Nano ESP32. Use the Espressif package above, not the separate Arduino ESP32 Boards package. The package URL is documented by [Espressif](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html).

```text
Pico GP0 / physical 1 / TX ──→ ESP32 GPIO16 / RX
Pico GP1 / physical 2 / RX ←── ESP32 GPIO17 / TX
Pico GND                  ─── ESP32 GND
```

Use these three signal wires. Each board has its own USB power. Disconnect USB before changing wires; do not join 5 V/VIN/3V3 rails. Existing SEN0325 GP6–GP13 wiring stays in place.

The current local Flash artifacts were verified by the integration task: Pico SHA-256 prefix **11958e93**, desktop ESP32 merged-image prefix **36610897**. These identify recorded build artifacts, not a guarantee of identical hashes from a differently named or configured rebuild.

The public handoff includes source and the [deployment/build manifest](gap_receiver/firmware/BUILD.json). The tested merged binary is retained privately because it embeds local compiler paths; it is not distributed. The recorded deployed hash remains valid and board firmware is unchanged. Follow the receiver README to compile and upload source with Arduino IDE; the receiver contains no motor actions.

After Flash, background Trial 03 matched **37/37** Pico/ESP records and **37** CRC-valid B ACKs; **36** had later Pico ACK telemetry. Following Pico software reboot, Trial 04 matched **14/14**, with **14** CRC-valid B ACKs and **13** later Pico confirmations. Each final packet reached the end of its recording before a later Pico report. Both trials had no interior missing observations, parse errors or observed receiver error/drop counter increases. All targets stayed invalid: this verifies communication/recovery, not acoustic direction accuracy. Read the [communication report](../reports/communication-2026-11-12/REPORT_EN.md).

| Location | Role |
|---|---|
| `gap_receiver/gap_receiver.ino` | Receive loop, ACK queue and USB diagnostics |
| `gap_receiver/gap_protocol.h` | CRC, session/sequence and 500 ms target freshness |
| `gap_receiver/gap_diagnostics.h` | Current-packet raw fields, distinct from target state |
| `gap_receiver/gap_self_tests.h`, `gap_receiver/tests/` | 57 shared startup/native checks |
| [Pico standalone](../pico-standalone/README.md) | Acoustic calculation, optional viewer and recording/analysis tools |

Raw diagnostics are not valid motor targets. See the receiver validity rules and the [communication notebook](../pico-standalone/COMMUNICATION_NOTEBOOK_EN.md). Original recordings, runtime logs and board backups stay outside this public handoff.
