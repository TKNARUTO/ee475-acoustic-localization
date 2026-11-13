# Gap UART 接收器 v1.1 — link_diag

更新：2026 年 11 月 12 日。[English](README_EN.md) · [概览](../README_ZH.md)

本程序接收 Pico 独立计算的 HF2 Gap 方向，检查数据包并返回 ACK。日志将本次收到的原始诊断和有效目标状态分开。它不在 ESP32 上计算声学方向，也不操作电机或 LED。

## 必须选对的板包

| 设置 | 已测试配置 |
|---|---|
| Arduino IDE / CLI | **2.3.8 / 1.4.1** |
| 开发板管理器中的包 | **esp32 by Espressif Systems**，版本 **3.3.12** |
| 开发板型号 | **NodeMCU-32S**，经典 ESP32 / NodeMCU ESP-32S |
| FQBN | `esp32:esp32:nodemcu-32s` |
| 附加开发板管理器网址 | `https://espressif.github.io/arduino-esp32/package_esp32_index.json` |
| 串口设置 | 115200 波特率；两板 UART 为 8N1 |

板包名、开发板型号、COM 端口是不同设置。需要 Espressif 的包，不是 Arduino ESP32 Boards / Nano ESP32 的包。本次板子不是 ESP32-S3。稳定版板包网址及安装步骤来源于 [Espressif 官方说明](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)。

## 三根线的接法

| Pico | 物理脚号 | 方向 | ESP32 |
|---|---:|---|---|
| GP0 / UART0 TX | 1 | → | GPIO16 / P16 / UART2 RX |
| GP1 / UART0 RX | 2 | ← | GPIO17 / P17 / UART2 TX |
| GND | 任意空闲 GND | ↔ | GND |

两板各自通过 USB 供电。改线前断开 USB，不互接 5 V/VIN/3V3 电源脚。SEN0325 原有 GP6–GP13 接线保持不变。USB 线不能替代这三根 UART 信号线。

## Arduino IDE 操作步骤

1. 打开 IDE **2.3.8**，进入 **File → Preferences → Additional Boards Manager URLs**（文件 → 首选项 → 附加开发板管理器网址），缺少上述稳定版网址时将它加入。
2. 打开 **Tools → Board → Boards Manager**，或左侧开发板管理器图标。搜索 `esp32`，选择 **esp32 by Espressif Systems**，安装 **3.3.12**。
3. 打开 `gap_receiver.ino`，同目录的配套头文件必须一起保留。
4. 选择 **Tools → Board → esp32 → NodeMCU-32S**。自动识别成其他型号时，通过 **Select other board and port** 手动设置。
5. 在 **Tools → Port** 选择实际的 ESP32 端口。本机示例是 **COM6**，其他人必须自行确认。最新本机 Pico 为 **COM8**，这是另一块设备。
6. 点击 **Verify** 验证编译。点击 **Upload** 前，关闭占用 ESP32 端口的串口监视器或日志程序，并保留已有 Flash 备份。
7. 打开 **Tools → Serial Monitor**，设置 **115200**。复位 ESP32 后应看到 `SELFTEST PASS checks=57 failed=0`，随后是 `READY EE475_GAP_RECEIVER v1.1 link_diag RX=16 TX=17 ... no_motor`。

手动选择方法参见 [Arduino 官方选板/端口说明](https://support.arduino.cc/hc/en-us/articles/4406856349970-Select-board-and-port-in-Arduino-IDE)。缺少 FQBN 时应选择开发板；端口不可用时应确认实际端口并关闭占用程序。

## 终端编译与上传

从当前 sketch 文件夹运行。先看 `board list`，再把 `COMx` 改为实际端口，不要照搬别人的 COM6。以下只是操作说明，不会自动执行。

```powershell
arduino-cli version
arduino-cli core list
arduino-cli board list
$EspPort = 'COMx'
arduino-cli compile --fqbn esp32:esp32:nodemcu-32s --output-dir '.\build\local' '.'
arduino-cli upload --fqbn esp32:esp32:nodemcu-32s --port $EspPort --input-dir '.\build\local' '.'
```

板包缺失时，使用上述 IDE 步骤，或执行：

```powershell
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.12 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

CLI 的 `upload` 不会先编译，应使用上一步成功编译的输出，见[官方上传命令说明](https://arduino.github.io/arduino-cli/1.4/commands/arduino-cli_upload/)。桌面的 Arduino 副本将主文件命名为 `sketch_nov12a.ino`；主 `.ino` 名称与 sketch 文件夹名称必须相同。

公开的 [BUILD.json](firmware/BUILD.json)保留已测试部署哈希、准确平台配置和源码身份。merged 二进制含本机编译路径，因此只在本机保存，不随项目分发。这次打包调整没有修改已测试的板上固件。桌面主文件与正式 `.ino` 内容相同，三个头文件也逐字一致；更换 sketch 名称仍可能改变重新构建的二进制元数据。请按上面的 Arduino IDE 步骤从公开源码编译上传，并先保留原 Flash 备份。本次没有提供未经测试的替代二进制。接收器没有电机控制，不适用于 ESP32-S3。

## 诊断与有效目标

```text
BEARING seq=11 class=DIAG_STALE ack_status=1 source_valid=0 raw_cdeg=12345 raw_q=678 source_age_ms=700 target_valid=0
```

`raw_cdeg=12345` 表示**阵列坐标中的 123.45°**。`raw_q` 是收到的 0..1000 质量值，不是准确率概率。`source_age_ms` 尚未包含接收器额外的 20 ms 余量。`source_valid` 是发送端标记；`target_valid` 才是接收器当前的目标状态。

| 分类 | 含义 |
|---|---|
| `ACCEPTED` | 新的有效包满足时效要求 |
| `DIAG_STALE` | 收到的年龄 + 20 ms 超过 500 ms，目标无效 |
| `DIAG_INVALID` | 年龄在范围内，但发送端明确标为无效，未提供详细原因 |
| `RX_REJECTED` | 无会话/会话不符，或重复、乱序；不能替换或续期目标 |

拒绝分类优先于过期分类。拒绝包显示 `target_valid=1` 时，可能表示此前目标尚未过期；原始字段仍属于这次被拒绝的包，不会把旧目标角度放到新序号下面。

无效 B 包可以保留有限原始拟合值用于诊断。**0° 本身也是合法方向。** 八个 B 字段没有 `fit_valid`、确认状态和详细原因，因此不能从零/非零数值推断是否有拟合。本版没有 D 包，诊断信息不授权运动。

## 协议与时效

ASCII，每帧含 LF 最多 128 字节。下面的 `\n` 表示一个 LF 字节：

```text
@H,1,SESSION8HEX*CCCC\n
@P,1,SESSION8HEX,seq*CCCC\n
@B,1,SESSION8HEX,seq,age_ms,valid,angle_cdeg,quality*CCCC\n
@A,1,SESSION8HEX,seq,type,status,count*CCCC\n
```

CRC16-CCITT-FALSE 只覆盖 `@` 与 `*` 之间的 payload：多项式 0x1021、初值 0xFFFF、不反射、无末尾异或；`123456789` → `29B1`。CRC/字段错误、CRLF、过长输入不会收到 ACK。解析失败行记录为 `RX_REJECTED reason=bad_frame`。

H 建立会话。新会话清除目标/序号状态，同会话重复 H 保留状态；H/P 不给测量续期。B 范围为：序号 uint32、年龄 0..60000 ms、valid 0/1、角度 0..35999 厘度、质量 0..1000。新的无效或过期 B 也推进序号，按 uint32 半范围规则比较；允许真实大幅转向。

ACK type：0 H、1 P、2 B。status：0 接受、1 明确无效、2 过期、3 重复/乱序、4 会话不符/未建立。count 对 H/P 和 status 为 0/1 的 B 累加。明确无效且过期的 B 仍返回 status=1；`DIAG_STALE` 只是显示分类。

```text
年龄 = source_age_ms + 20 ms + 收到后经过的时间
年龄 > 500 ms 时目标过期
```

限制没有放宽。阵列与车头方向还需要标定；这里也没有验证电机停机时间。

## 验证与限制

共享原生/启动检查 **57 项通过**。启动检查在 UART2 启用前使用临时状态执行。当前本机已核验 Flash 文件的哈希前缀为：Pico **11958e93**、桌面 ESP32 merged 镜像 **36610897**。

Flash 后 Trial 03：**37/37 字段完全一致**、**37 个正确 CRC B ACK**、**36 个后续 Pico 确认**。Pico 软件重启后的 Trial 04 对应为 **14/14、14、13**。每次最后一包都遇到录制结束，未等到后续 Pico 日志。无中间缺项、解析错误和接收器错误/丢弃计数的观测增量，会话与序号恢复正常。目标一直无效，因此验证的是通信与恢复，不是声学角度准确率。详见[通信报告](../../reports/communication-2026-11-12/REPORT_ZH.md)。

此前手机测试的启动 USB 输出有大量重复和拼接残行，不能把整轮当成干净验收。新版录制器会单独保存有字节预算的启动数据，对每个端口清理一次输入缓冲、对齐 LF 后才正式计时，不会过滤测试中途的错误。这并不能证明 FTDI 驱动有问题。

USB 日志是尽力写入，繁忙时可能丢弃；检查 `STAT bad`、`lines`、`ack_drop`、`usb_drop`。USB TX 缓冲为 512 字节，ACK 队列最多四帧。ESP ACK 日志证明已生成/排队；后续 Pico ACK 字段补充收到回执的证据。ACK 往返时间含前台解析等待，不等于纯线缆延迟。

| 文件 | 功能 |
|---|---|
| `gap_receiver.ino` | 接收/ACK 循环与 USB 诊断 |
| `gap_protocol.h` | 协议状态机，v1.1 诊断未修改它 |
| `gap_diagnostics.h` | 本次原始数据的纯格式化及分类 |
| `gap_self_tests.h` | 共享 57 项回归检查 |
| `tests/host_protocol_test.cpp` | 原生测试入口，不访问串口/GPIO |
| `README_EN.md`、`README_ZH.md` | 安装与交接 |
| `firmware/` | 部署证据、构建和源码哈希；已测试二进制只在本机保存 |
| `build/`（如存在） | 本机生成文件，不是源码或已安装证明 |

来源与决策见[通信笔记](../../pico-standalone/COMMUNICATION_NOTEBOOK_ZH.md)。原始录音和备份保留在公共项目外。符合时效的声学目标验收、测距和电机控制仍是后续工作。
