# EE475 声音定位项目
**本阶段：Pico 独立计算＋ESP32 通信，2026 年 11 月 12 日**

手机播放 HF2 间隔信标，SEN0325 输出原始麦克风数据。现在由 **Pico 自己采集并计算方向**，再把结果发送给 ESP32。电脑只负责显示。ESP32 当前只接收、确认和管理结果有效期，还没有执行声学计算或控制电机。

**阶段结论：**两板通信字段一致，持久固件已核验，不打开 Pico 的电脑串口也能持续通信。但还不能作为可直接跟随的小车控制版本：本次测量的结果仍超过新鲜度门限，控制目标有效标志全部为 0，0.2–0.5 秒延迟目标尚未完成。详见[测试报告](reports/communication-2026-11-12/REPORT_ZH.md)。

## 平台、板卡包与端口
| 部分 | 硬件／平台 | 本次使用工具 | 板型／端口 |
|---|---|---|---|
| Pico 定位 | Raspberry Pi Pico，RP2040，C/C++ | Pico SDK **2.3.1**；Arm GNU **14.2.Rel1 / GCC 14.2.1**；CMake **4.4.4**；Ninja **1.13.2**；picotool **2.3.1** | SDK 板型 **pico**；本机目前 **COM8**，此前为 COM5 |
| ESP32 接收 | 38 针 **NodeMCU ESP-32S**，经典 ESP32-D0WD-V3，4 MiB Flash | **Arduino IDE 2.3.8**；CLI **1.4.1**；**esp32 by Espressif Systems 3.3.12** 板卡包 | Arduino 板型 **NodeMCU-32S**；FQBN **esp32:esp32:nodemcu-32s**；本机 **COM6** |
| 电脑监视器 | Windows，Python＋Tk | Python **3.12.4**；pyserial **3.5**；离线验证／图表另用 NumPy、Matplotlib | 自动识别一块 Pico，不占用 ESP32 端口 |
| 手机播放器 | Android 8／API26 以上；测试者使用 S25 Ultra | Beacon Loop **1.2**；Java；编译／目标 API **35** | APK 和源代码在 android-player |

**NodeMCU-32S 是板型，esp32 是板卡包，COM6 是这台电脑分配的端口。**这块板不是 ESP32-S3，不要选 Arduino Nano ESP32 或 ESP32S3 Dev Module。换电脑、USB 模式后端口可能变化。Pico 使用 Pico SDK 工程，不是 Arduino sketch。

- [ESP32 的 Arduino 安装、编译和上传](esp32-link/gap_receiver/README_ZH.md)
- [Pico 构建、烧录与算法选项](pico-standalone/README_ZH.md)
- [电脑监视器安装](docs/SETUP_WINDOWS_ZH.md)
- [安卓播放器使用与构建](android-player/README_ZH.md)

## 启动步骤
1. 先断电，按[完整接线表](docs/HARDWARE_ZH.md)检查。保留原阵列接线。
2. 两板各自用 USB 供电，板间只接 **Pico GP0/TX → ESP P16/RX**、**Pico GP1/RX ← ESP P17/TX**、**GND ↔ GND**。不接板间电源线。
3. 如需安装固件，按各板说明单独烧录。根目录启动入口不会写固件。
4. 双击 **Start.cmd** 打开／聚焦监视器；**Update.cmd** 检查本地代码并重启监视器，不会从 Git 下载更新。Pico 上电自动扫描；关闭窗口后仍继续运行；Pause／Resume 才会发送暂停／恢复采集命令。
5. 手机安装 [BeaconLoop-1.2.apk](android-player/releases/BeaconLoop-1.2.apk)，选择 **Use HF2 gap beacon**，Normalize 保持关闭，点击 Play；也可循环播放[参考 WAV](audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav) 或 [MP3](audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3)。
6. 对比测试时固定手机角度、距离和音量，再有计划地暂停／恢复。要记录真实角度才能评估物理精度。黄色诊断箭头不是新鲜控制命令。

固定信号为 **18–22 kHz**、48 kHz 采样率，每周期 4096 点：2048 点发声＋2048 点静音，各约 42.67 ms。设计中的静音不等于断联。播放器允许导入别的音频，但当前 Pico 不会自动学习新信标，仍需匹配编译进固件的参考。高频是否可听、能传多远都取决于人和设备。

## 目录与角色
| 目录 | 用途 |
|---|---|
| pico-standalone/ | 当前 Pico 源码、固定 HF2 算法、测试、UF2 和可选电脑监视器 |
| esp32-link/gap_receiver/ | 独立 Arduino sketch：UART 接收、ACK、诊断与过期处理，无电机控制 |
| android-player/ | Java 源码、APK、本地音频导入、循环播放与可选有限增益 |
| audio/phone/HF2-gap-test/ | 与接收端配套的 WAV／MP3 |
| docs/ | 中英文安装、接线、架构和队友／AI 交接 |
| reports/communication-2026-11-12/ | 中英文报告、实测指标和对比图 |
| tools/ | 启动、目录清单和发布检查工具 |
| references/ | 原始硬件／项目资料，不代表当前固件操作说明 |
| legacy/pico+computer combo sensoring version/ | 唯一保留的旧版：最终电脑计算＋Pico 采集模板；旁边是对应 ZIP |

[文件清单](docs/FILE_CATALOG_ZH.md)逐项说明可分享文件与作用。代码和界面使用英文；说明文书分别命名 EN／ZH；机器读取的清单保留单份。

## 交接与未完成内容
请读[队友／AI 交接](docs/TEAM_HANDOFF_ZH.md)、[架构与预计问题](docs/INTEGRATION_ZH.md)、[验证说明](docs/VALIDATION_ZH.md)和[通信阶段笔记](pico-standalone/COMMUNICATION_NOTEBOOK_ZH.md)。笔记记录需求理解、设计决定、验证依据和剩余问题。

旧电脑组合版本仍是有用的模板，之前测试的更新周期更短。当前 Pico 计算只用一个核心；FFT／双核优化暂时停止，本阶段先把通信保存完整。不能为了让箭头变绿而取消新鲜度检查，也不能仅因角度变化大就拦截方向。本阶段不包含测距、电机控制、避障和自动跟随闭环。

原始录音、逐次日志、密钥、工具链和板卡原固件备份只留本地。旧版本在移出活跃项目时已验证哈希；GitHub 只同步可分享文件，见[发布说明](docs/SHARING_ZH.md)。
