# Pico 独立声音定位：使用说明与状态

更新：2026-11-12，记录到 Flash trial 05（无 Pico USB 读者）。[English](README_EN.md) · [通信笔记](COMMUNICATION_NOTEBOOK_ZH.md) · [设计依据](DESIGN_NOTEBOOK_ZH.md)

Pico 采集 SEN0325、识别固定 HF2 Gap 信标并计算方向，ESP32 接收方向/状态并回执；电脑只是可选监控。当前用现有两块板和已测 FAST 算法验证通信，暂停进一步 FFT 和双核优化。本阶段没有电机、避障或距离控制代码。

## 实际平台和工具

| 组件 | 已核对配置 |
|---|---|
| Pico 目标板 | Raspberry Pi Pico / RP2040，120 MHz core0；`PICO_BOARD=pico`、`PICO_PLATFORM=rp2040` |
| Pico 框架 | **原生 C11/C++17 + Pico SDK 2.3.1，不是 Arduino sketch**；SDK commit `079c6f39023649b154152db30f1d781e884879bc` |
| Pico 实际编译器 | Arm GNU Toolchain **14.2.Rel1** build arm-14.52；GCC/G++ **14.2.1** 20241119 |
| 构建工具 | CMake **4.4.4**；Ninja **1.13.2.git.kitware.jobserver-pipe-1** |
| Pico 写入工具 | picotool **2.3.1** |
| ESP32 板型 | **NodeMCU-32S / 经典 ESP32，不是 ESP32-S3**；FQBN `esp32:esp32:nodemcu-32s` |
| ESP32 编辑/构建 | Arduino IDE **2.3.8**；Arduino CLI **1.4.1**；开发板包 **esp32 by Espressif Systems 3.3.12** |
| ESP32 写入工具 | esptool **5.5.0** |
| 可选电脑监控 | Python **3.12.4**、pyserial **3.5** |
| 本机端口 | Pico Flash **COM8**、ESP32 **COM6**；此前 RAM 是 COM5。其他电脑或重新枚举后要重新检测。 |

Pico 编译器版本来自实际 CMake 构建记录，不是 PATH 中任意另一份 GCC。离线原生测试使用 Cygwin GCC 4.8.3，不是板上固件编译器。

## 接线

| Pico | ESP32 NodeMCU-32S | 方向 |
|---|---|---|
| GP0，物理 1 脚 | P16 / GPIO16 | Pico TX → ESP32 RX |
| GP1，物理 2 脚 | P17 / GPIO17 | Pico RX ← ESP32 TX |
| GND，如物理 3 脚 | GND | 共地 |

115200 8N1、3.3 V 电平。SEN0325 原有 GP6–GP13 接线不变。两板分别 USB 供电，不接板间 3V3、5V、VIN；ESP32 另印的 RX/TX 控制台脚不是 P16/P17。改线前断电。

## 启动和音频

公开的 [Pico v0.2 Flash UF2](firmware/pico_gap_standalone-v0.2.uf2) SHA256 为 `11958e9310926e856f01359c10c4832cffc046cb64a8edebe675b76e3984caa0`，与已写入并校验的镜像一致。请一起保留 [构建/源码身份记录](firmware/BUILD.json) 和 [资源审计](firmware/resource-audit.json)。[ELF](firmware/pico_gap_standalone-v0.2.elf) 用于调试，UF2 用于写入；该镜像使用下述明确的 FAST 选项，不是 W1C1。

项目根目录 `Start.cmd` 打开 **Pico Standalone Monitor**；`Update.cmd` 检查本地监控源码并正常重启窗口，不下载远程 Git 更新。这两个入口不烧录，也不运行旧电脑定位。外层 EE475 保留原中文命名的转发入口；项目根目录只保留 Start.cmd 和 Update.cmd。每个串口只保留一个读者；有限时长双串口记录器用于通信实验，不需要 GUI 自动化。

Pico 自动扫描，监控可暂停/恢复并设置仅影响显示的车头参考。绿色箭头需要已确认的新鲜结果；橙色是诊断拟合，不能当控制目标。第二张图是 DSP 各阶段耗时，不是七通道原始声波。

手机循环播放 `audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3` 或对应 WAV。Pico 模板固定；手机播放器导入其他文件不等于 Pico 支持定位它。保留 18–22 kHz、48 kHz 采样和 4096 帧窗口。

## 构建

通信版使用 `GAP_INTEGER_FFT=ON`、`GAP_INTEGER_FAST=ON`、`GAP_WHITEN_FLOAT=OFF`、`GAP_MAG_CACHE=OFF`。在项目根目录运行，SDK 路径改成自己的安装目录：

```powershell
cmake -S pico-standalone -B build/pico-flash -G Ninja -DPICO_SDK_PATH="<pico-sdk-dir>" -DPICO_BOARD=pico -DPICO_PLATFORM=rp2040 -DPICO_NO_FLASH=OFF -DGAP_INTEGER_FFT=ON -DGAP_INTEGER_FAST=ON -DGAP_WHITEN_FLOAT=OFF -DGAP_MAG_CACHE=OFF
cmake --build build/pico-flash
arduino-cli compile --fqbn esp32:esp32:nodemcu-32s esp32-link/gap_receiver
```

RAM 临时镜像用 `PICO_NO_FLASH=ON` 和另一构建目录；上面只是构建命令，不会烧录。float 基线可用 `GAP_INTEGER_FFT=OFF` 保留。源码快照、flags、工具版本和镜像哈希要一起核对，不能从新源码推断板上版本。W1C1 仅离线验证/构建，双核没有实现。

DSP 工作区共享且不可重入，目前只用 core0。链接剩余 heap 和函数静态栈大小不是运行时余量；控制环还需真实时限和反馈验证。580 窗整数/float 对照判定一致，最大角差 0.036026°；同频错误码误检仍未解决，这不是物理方向误差保证。

## 当前证据与部署

| 检查 | 结果 | 限制 |
|---|---|---|
| Pico main / link / ESP 原生测试 | 107 / 41 / 57 项通过 | 不等于实板或声学验收 |
| RAM trial 01，背景 | 38 条精确匹配，37 次后续 Pico ACK 确认 | 尾边界不确定性仍保留 |
| RAM trial 02，手机 | 34 TX 中 33 条精确匹配，32 次后续回执；32/34 有拟合，全部七麦码命中 | 4453 条重复启动前缀和 1 条坏 STAT，**整体未通过** |
| Flash trial 03，暖机背景 | 37/37 精确匹配，37 个 CRC 正确 ACK、36 次后续确认；无解析错误/内部缺项 | 仅验证该背景观察 |
| Flash trial 04，软件重启 | 新 session，14/14 精确匹配，14 个 CRC 正确 ACK、13 次后续确认；无解析错误 | **不是物理断电测试** |

trial 03 暖机收集 9063 B，1.125 s 后按 LF 对齐开始正式观察，没有中途去重。边界记录数量差不能直接算 UART 丢包率。trial 05 仅读 ESP COM6 共 12.109 s，不打开 Pico USB：收到 15 条连续 BEARING seq48–62、14 个 CRC 正确 ACK seq49–62，观察到的 bad/lines/ack_drop/usb_drop 均为 0。它证明无 Pico 读者仍持续发送，不等于拔掉 USB 数据线或独立电源冷启动；暖机手机试播仍另测。

Pico Flash `11958e9310926e856f01359c10c4832cffc046cb64a8edebe675b76e3984caa0` 已用 picotool 写入并校验。ESP32 桌面草稿合并镜像 `36610897ee2f78f5fe8153d043df68cbb00b5a7cf040c7d3475dc2b3d77cda6b` 已写入并哈希验证。此前 RAM 镜像为 `7822b95524771d02305743715eeb17d09938065297edf0ed902e99ea9ddc8fb9`。

trial 02 的 DSP/cycle/age 中位数为 **789.160 / 884.558 / 834 ms**；trial 03 背景为 **719.932 / 809.641 / 765 ms**。信号条件不同，不能把它们当等输入的优化比较。**0.2–0.5 s 真实延迟仍未达标**；尚无可用控制目标，年龄超过 500 ms，周期也超过 750 ms 确认间隔。拟合比例不是方向准确率，ACK RTT 不是声音到转向延迟。

## 数据含义与恢复

USB 输出 `GAP`、`PROFILE` 和按请求返回的 `STATUS`；分别报告 `fit_valid`、`confirmed`、最终 `valid`。成功 TX 字段为 `tx_result_seq`、`tx_age_ms`、`tx_valid`、`tx_angle_cdeg`、`tx_quality`；后续 B 回执用 `ack_seq`、`ack_roundtrip_us`、`ack_status` 关联。失败发送不伪造成功 TX，H 回执不覆盖 B 信息，H/P 不延长旧方向寿命。RTT 包含主循环解析延迟。

[八字段 B 协议](../esp32-link/gap_receiver/README.md) 含会话、序号、年龄、有效性、角度、质量与 CRC16。`valid=0` 时，过期/未确认的有限拟合保留 raw 诊断；无拟合、采集无效或非有限数值发 0。ESP 把 raw 与 `target_valid` 分开。0° 也是合法方向；只看 B 无法判断 fit、确认状态和详细原因。invalid 不是正前方命令。

年龄从窗口中心算，有效期 500 ms 含 20 ms 通信预算，两次码命中需小于 750 ms。不因角度变化大而拒绝，也未放宽有效期掩盖慢计算。写入前 Pico 2 MiB 和 ESP32 4 MiB 原镜像已私有备份并核对。Flash 软件重启已观察，独立供电冷启动仍另测。

## 文件职责与历史保留

| 文件/目录 | 作用 |
|---|---|
| `main.c`、`standalone_link.h` | 自主采集/调度、UART 元数据、CRC、年龄与确认 |
| `sen0325_i2s.pio` | 同步麦克风采样 |
| `dsp/`、`CMakeLists.txt` | 纯 C 算法、固定模板、FFT 与原生 SDK 构建选项 |
| `tests/`、`experiments/` | 离线验证和独立实验 |
| `tools/desktop.py`、`tools/desktop_control.py` | 可选监控、启动与更新 |
| `tools/monitor.py` | 有限时长串口采集 |
| `DESIGN_NOTEBOOK_EN.md` / `_ZH.md` | 算法、资源和第 11 节带宽预算 |
| `COMMUNICATION_NOTEBOOK_EN.md` / `_ZH.md` | 通信决策、实测与待验收项 |
| `logs/` | 私有运行日志，不公开分发 |

本机授权桌面副本 `sketch_nov12a` 含接收器 `.ino`、`gap_protocol.h`、`gap_diagnostics.h`、`gap_self_tests.h`、`sketch.yaml`。独立编译占程序空间 277624 B、全局变量 22932 B，不是实时剩余内存；其合并镜像已写入验证。原空白草稿已私有备份，EE474 源码和原电机程序未改。

保留 [成熟 Pico + 电脑版](../legacy/pico+computer%20combo%20sensoring%20version/README.md) 及旁边 ZIP、计算 checkpoint `pico-standalone-compute-checkpoint-2026-11-12`（维护者外部本地归档，不随公开项目分发）。旧版会加载 v0.6 RAM 采集镜像、在电脑定位，不是当前工作流。

原始日志、录音、设备备份为 **local evidence, not shipped**。公开摘要规划在 `reports/communication-2026-11-12/`，含 `REPORT_EN.md`、`REPORT_ZH.md`、`metrics.json`、`figures/`。共享文档不保留个人绝对安装路径；集成前请查看尚未解决的错码误检与物理准确度限制。

## 整理后的公开回放验证

公开 runner 使用保留的成熟 PC 参考和 `--skip-real` 重新运行：**187 窗、29 项检查，27 项通过、2 项已知错码拒绝失败**。组成是 144 全圆、37 拒绝样本、3 重复错码、3 大转向；拒绝组有 1/37 负样本误受，重复错码组有 3/3 误受。四组 C 与 Python arrival 的有效性差异均为 0，因此总体算法验收仍未通过。

这次使用默认 **float** 源码构建，不是正在板上运行的 FAST，也跳过私有录音。它验证公开文件可复现并保留已知检测缺陷，不是新的硬件速度或物理准确度测量。5 项参考路径检查通过；生产 PNR 仍为 12.5 dB。

```text
python pico-standalone/tests/run_offline_validation.py --skip-real --gcc <host-gcc> --output <external-output>
```

默认参考是 `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup`，可用 `--reference-app` 覆盖。旧 standalone 实验和私有计算 checkpoint 已外部保留，不作为当前公开目录中的活动文件。

## 复现原生通信检查

使用**电脑本机 GCC**（本次记录为 Cygwin GCC 4.8.3），不要用 ARM 交叉编译器。在项目根目录运行：

```powershell
python pico-standalone/tests/test_main_communication.py --gcc "<host-gcc-executable>" --output-dir "<external-test-output>/main"
# 运行生成程序时，保证本机编译器 runtime/DLL 目录在 PATH 内。
& "<host-gcc-executable>" -std=c11 -O2 -Wall -Wextra pico-standalone/tests/host_link_test.c -o "<external-test-output>/host_link_test.exe"
& "<external-test-output>/host_link_test.exe"
```

先创建项目外的输出目录。Python runner 按自身位置发现当前 Pico 源码，给子进程 PATH 加入编译器目录，并拒绝在项目内部生成输出。它提取真实 main 函数，不另写一份镜像逻辑；只模拟 UART、时钟和 USB。重新执行结果：**107 项 main 断言通过**，最大测试 GAP 行 **699 B**；**41 项 link 检查通过、0 失败**。未运行 DSP、未打开串口或操作板子。编译输出和源码哈希写在项目外，原生运行时间不是 Pico 时间。

## 首次安装

见[持久固件安装](firmware/README_ZH.md)，包括 BOOTSEL／RPI-RP2 或 picotool 装载、备份要求与本次 UF2。电脑启动入口不会安装固件。
