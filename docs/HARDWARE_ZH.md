# 硬件与 GPIO
## 当前板卡
Pico 是 Raspberry Pi Pico／RP2040；阵列是 DFRobot SEN0325／Sipeed R6+1，六个外围麦克风加一个中心麦克风。接收板是照片中的 38 针 NodeMCU ESP-32S，芯片 ESP32-D0WD-V3 rev3.1，4 MiB Flash。Arduino 板型选 NodeMCU-32S，板卡包是 esp32 by Espressif Systems 3.3.12，不是 ESP32-S3。

## 阵列接 Pico
| 阵列标识 | Pico 信号 | 物理针号 | 作用 |
|---|---|---|---|
| VIN | 3V3 OUT | 36 | 沿用当前麦克风测试供电 |
| GND | GND | 13 | 地 |
| MIC_D0 | GP6 | 9 | I2S 数据 0 |
| MIC_D1 | GP7 | 10 | I2S 数据 1 |
| MIC_D2 | GP8 | 11 | I2S 数据 2 |
| MIC_D3 | GP9 | 12 | I2S 数据 3 |
| MIC_CK | GP10 | 14 | Pico 输出位时钟 |
| MIC_WS | GP11 | 15 | Pico 输出字选择 |
| LED_CK | GP12 | 16 | 保留 LED 时钟，灯环关闭 |
| LED_DA | GP13 | 17 | 保留 LED 数据，灯环关闭 |

Pico 元件面朝上、USB 在上时，左列 GP0–GP15，右列 VBUS–GP16。背面照片左右相反。GPIO 编号、物理针号和面包板行号不是一回事。阵列接口从带文字的一面看：
```text
LED_DA    LED_CK
MIC_D1    MIC_D0
MIC_D3    MIC_D2
MIC_CK    MIC_WS
GND       VIN
```
沿用已经工作的 3.3 V 麦克风测试供电；相关硬件修订的 VIN 资料存在区别。本阶段没有验证 5 V 供电或完整灯环电流。不要把 36 脚 3V3 OUT 和 37 脚 3V3_EN 接反。

## Pico 与 ESP32：只增加三根线
| Pico | ESP32 丝印 | 方向 |
|---|---|---|
| GP0／物理1／UART0 TX | P16／GPIO16／UART2 RX | Pico 结果发往 ESP |
| GP1／物理2／UART0 RX | P17／GPIO17／UART2 TX | ESP 确认发往 Pico |
| GND，如物理3 | GND | 共地 |

115200 波特率、8 位数据、无校验、1 位停止，3.3 V 逻辑。改线先断电；各板用各自 USB 供电，不互接 VBUS／5V／3V3。GP6–GP13 不变。其他 ESP 模块可能把 16／17 用作 PSRAM，换板前需重新核对。

## 声道与带宽约定
顺序：D0L(0°)、D0R(60°)、D1L(120°)、D1R(180°)、D2L(240°)、D2R(300°)、D3R(中心)；D3L 空置。40 mm 外圈半径、343 m/s 声速只是模型假设，仍需实际安装校准。

BCLK 为 3.072 MHz，WS 为 48 kHz。四根并行数据线总共 12.288 Mbit/s；DMA 按八个 32 位填充槽保存，为 1.536 MB/s；七声道 PCM16 相当于 672 kB/s。4096 点七声道缓冲为 57,344 B；每个 DMA 块 512 帧／16 KiB／10.667 ms，双缓冲 32 KiB。

UART 只传方向摘要，不传原始音频。B 包最长 49 B，ACK 最长 45 B。假设每秒 5 个结果，B 流量 245 B/s，占单向 11,520 B/s 有效载荷能力约 2.13%。这是规划预算，不代表当前已经达到 5 Hz。详见[架构](INTEGRATION_ZH.md)。
