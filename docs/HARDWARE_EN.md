# Hardware and GPIO
## Current platforms
Pico: Raspberry Pi Pico / RP2040. Array: DFRobot SEN0325 / Sipeed R6+1, six outer microphones plus center. Receiver: photographed 38-pin NodeMCU ESP-32S, classic ESP32-D0WD-V3 rev3.1, 4 MiB Flash. Arduino board selection is NodeMCU-32S, package esp32 by Espressif Systems 3.3.12. It is not ESP32-S3.

## Array → Pico
| Array label | Pico signal | Physical pin | Role |
|---|---|---|---|
| VIN | 3V3 OUT | 36 | Existing microphone test supply |
| GND | GND | 13 | Ground |
| MIC_D0 | GP6 | 9 | I2S data 0 |
| MIC_D1 | GP7 | 10 | I2S data 1 |
| MIC_D2 | GP8 | 11 | I2S data 2 |
| MIC_D3 | GP9 | 12 | I2S data 3 |
| MIC_CK | GP10 | 14 | BCLK from Pico |
| MIC_WS | GP11 | 15 | WS from Pico |
| LED_CK | GP12 | 16 | Reserved LED clock; illumination off |
| LED_DA | GP13 | 17 | Reserved LED data; illumination off |

Component side facing you, USB at top: Pico left row GP0–GP15, right row VBUS–GP16. The underside photo reverses left/right. GPIO numbers are not physical pin numbers or breadboard row numbers. On the array connector, viewed from its labelled side:
```text
LED_DA    LED_CK
MIC_D1    MIC_D0
MIC_D3    MIC_D2
MIC_CK    MIC_WS
GND       VIN
```
Keep the existing working 3.3 V microphone-test configuration; related board revisions have different VIN documentation. This milestone does not validate 5 V supply or full LED-ring current. Do not confuse 3V3 OUT pin36 with 3V3_EN pin37.

## Pico ↔ ESP32 — only three wires
| Pico | ESP32 silkscreen | Role |
|---|---|---|
| GP0 / physical1 / UART0 TX | P16 / GPIO16 / UART2 RX | Pico result → ESP |
| GP1 / physical2 / UART0 RX | P17 / GPIO17 / UART2 TX | ESP ACK → Pico |
| GND, e.g. physical3 | GND | Common reference |

115200 baud, 8 data bits, no parity, 1 stop bit; 3.3 V logic. Disconnect power before rewiring. Power each board by its own USB. Do not connect their VBUS/5V/3V3 rails. Keep GP6–GP13 unchanged. A different ESP module can reserve GPIO16/17 for PSRAM; recheck before transplanting this wiring to another board.

## Channel and bandwidth contract
Order: D0L(0°), D0R(60°), D1L(120°), D1R(180°), D2L(240°), D2R(300°), D3R(center). D3L is unused. Nominal outer radius 40 mm and sound speed 343 m/s are model assumptions, not a mechanical calibration certificate.

BCLK 3.072 MHz; WS 48 kHz. Four data lines × 2 slots × 32 bits × 48 kHz = 12.288 Mbit/s across the parallel wires. DMA stores 1.536 MB/s (8 padded 32-bit slots); seven PCM16 channels would be 672 kB/s. A 4096-sample seven-channel buffer is 57,344 B; a 512-frame DMA block is 16 KiB every 10.667 ms; two blocks use 32 KiB.

The UART carries compact bearing packets, not raw audio: ≤49 B for B, ≤45 B for ACK. At 5 results/s, B traffic is 245 B/s, about 2.13% of one direction's 11,520 B/s payload capacity. These are design budgets, not a measured 5 Hz result rate. See the [architecture](INTEGRATION_EN.md).
