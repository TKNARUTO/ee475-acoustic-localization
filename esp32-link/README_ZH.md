# Pico 与 ESP32 通信

更新：2026 年 11 月 12 日。[English](README_EN.md)

当前流程是 **手机声音 → SEN0325 → Pico 独立计算 → ESP32 接收与回执**。Pico 采集阵列并计算 HF2 Gap 方向，电脑只作为可选监视端。ESP32 收到数据后返回 ACK；电机控制与测距仍属于后续集成。

安装、接线、上传及协议说明见 [gap_receiver/README_ZH.md](gap_receiver/README_ZH.md)。当前源码入口只有 `gap_receiver/`；旧的低频 ESP32 示例已退出本次交接流程。

| 项目 | 当前配置 |
|---|---|
| 硬件 | NodeMCU ESP-32S，经典 ESP32 |
| IDE / CLI | Arduino IDE **2.3.8** / Arduino CLI **1.4.1** |
| 开发板管理器中的包 | **esp32 by Espressif Systems 3.3.12** |
| 开发板 / FQBN | **NodeMCU-32S** / `esp32:esp32:nodemcu-32s` |
| 稳定版板包索引 | `https://espressif.github.io/arduino-esp32/package_esp32_index.json` |
| UART | 115200、8N1；ESP32 RX16、TX17 |
| 端口 | 本机示例为 ESP32 COM6、Pico COM8；其他电脑必须自行确认实际端口 |

**板包、开发板型号和 COM 端口是三个不同设置。** 本板不是 ESP32-S3 或 Arduino Nano ESP32。需要安装上述 Espressif 包，不是另一个 Arduino ESP32 Boards 包。板包网址来源于 [Espressif 官方说明](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)。

```text
Pico GP0 / 物理脚1 / TX ──→ ESP32 GPIO16 / RX
Pico GP1 / 物理脚2 / RX ←── ESP32 GPIO17 / TX
Pico GND               ─── ESP32 GND
```

两板之间只接这三根信号线，各自通过 USB 供电。改线前拔掉 USB，两板的 5 V/VIN/3V3 不互接。SEN0325 原有 GP6–GP13 接线保持不变。

主集成任务已核验当前 Flash 镜像：Pico SHA-256 前缀 **11958e93**，桌面 ESP32 merged 镜像前缀 **36610897**。这些前缀标识已记录的构建文件，不表示改工程名或工具配置重新编译后哈希一定相同。

公共项目提供源码和[部署/构建清单](gap_receiver/firmware/BUILD.json)。已测试的 merged 二进制含本机编译路径，因此保留在本机，不随项目分发；已记录的部署哈希仍有效，板上固件没有改变。请按接收器说明用 Arduino IDE 从源码编译上传，它只做台架接收，没有电机动作。

Flash 后的背景 Trial 03 为 **37/37** 条 Pico/ESP 字段完全一致、**37** 个正确 CRC 的 B ACK、**36** 个后续 Pico 回执确认。Pico 软件重启后的 Trial 04 为 **14/14** 一致、**14** 个正确 CRC ACK、**13** 个后续确认。每次最后一包都到达了录制结束边界，来不及观察下一条 Pico 日志。两次均无中间缺项、解析错误和接收器错误/丢弃计数的观测增量。所有目标仍为无效，因此验证的是通信与恢复，不是角度准确率。详见[通信报告](../reports/communication-2026-11-12/REPORT_ZH.md)。

| 位置 | 功能 |
|---|---|
| `gap_receiver/gap_receiver.ino` | 接收循环、ACK 队列、USB 日志 |
| `gap_receiver/gap_protocol.h` | CRC、会话/序号和 500 ms 目标时效 |
| `gap_receiver/gap_diagnostics.h` | 本次收到的原始字段，与有效目标状态分开 |
| `gap_receiver/gap_self_tests.h`、`gap_receiver/tests/` | 57 项共享启动/原生检查 |
| [Pico 独立版](../pico-standalone/README.md) | 声学计算、可选界面和录制/分析工具 |

原始诊断不是有效电机目标。请继续阅读接收器时效规则及[通信笔记](../pico-standalone/COMMUNICATION_NOTEBOOK_ZH.md)。原始录音、运行日志和板子备份保留在公共项目之外。
