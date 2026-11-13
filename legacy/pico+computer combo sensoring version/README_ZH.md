# 保留的电脑＋Pico 声音定位模板

这是最终保留的电脑运算版本：手机播放 HF2 gap，SEN0325 接收声音，Pico 采集七通道音频，Windows 电脑计算并显示方向。当前 Pico／ESP32 独立版本不在此模板中。

```mermaid
flowchart LR
 Phone[手机播放] --> Array[SEN0325 阵列]
 Array --> Pico[Pico 同步采集]
 Pico -->|USB PCM + CRC32| PC[Windows 计算方向]
 PC --> View[方向和信号图]
```

## 启动

1. 将 ZIP 完整解压到可写目录，保留相对目录结构。
2. 按[Windows 安装说明](docs/SETUP_WINDOWS_ZH.md)配置，再核对[接线表](docs/HARDWARE_ZH.md)。
3. 接入指定 Pico。必要时按住 BOOTSEL 接入 USB，看到 RPI-RP2 磁盘；旧启动器会检查并加载随包 RAM 固件。
4. 打开 `一键启动.cmd`，点击 **Start Scan**。`Update.cmd` 只检查并重启本地旧接收程序，不下载更新，也不启动新独立版本。
5. 用手机循环播放匹配的 [HF2 gap 音频](audio/phone/HF2-gap-test/README_ZH.md)。电脑只接收，不播放信标。

## 固件来源必须区分

随包可运行 UF2／ELF 为 **v0.6-RX2**。UF2 的 SHA-256 为 `76470847618d44065001eba3615cf49e19e858a27839dd09543700e7d8471151`。数据仅写入 SRAM，**断电后必须重新加载**。

相邻 `main.c`、`CMakeLists.txt` 和 `link_frame.h` 是 **v0.8-BRIDGE 开发源码**，不能声称它们能重建随包 v0.6 固件。直接运行 Build.ps1 不等于复现 v0.6；比较旧表现时应保留已验证的二进制。可选桥接配置仍为 `enabled: false`，此模板不包括电机控制或 Pico 独立方向计算。

## 看结果与交接

HF2 gap 频带为 18–22 kHz，采样率 48 kHz；每周期 4096 点，其中发声 2048 点、静音 2048 点。静音半段是设计内容。停留的箭头不是新测量，雷达圆圈不是距离。高频输出、可听性、反射和朝向需要实测；真实的大角度转向仍然允许。

参阅[使用说明](docs/USER_GUIDE_ZH.md)、[验证说明](VALIDATION_ZH.md)、[文件目录](FILE_CATALOG_ZH.md)、[智能体交接](AGENTS_ZH.md)和[平台要求](PLATFORM_ZH.md)。SOURCE_MANIFEST.json 保留原来源和本次文书修订关系；SHA256SUMS.txt 校验除自身外的全部文件。私有录音、日志、自选音频、密钥和工具链不在归档中。

平台与工具：电脑端使用 Windows 10/11、Python 3.12+（含 Tcl/Tk）；Pico 通过 USB 采集。手机播放器需 Android 8.0/API 26 或以上。运行旧固件不需要编译器；工具版本及限制见[平台说明](PLATFORM_ZH.md)。当前独立 Pico 程序位于模板根目录上两级的 `pico-standalone/`，不包含在本 ZIP 内。
