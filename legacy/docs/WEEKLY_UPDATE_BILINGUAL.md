# EE475 Weekly Update — Acoustic Localization

**Project:** Tagalong Following Robot  
**Week ending:** 17 October 2026  
**Assigned subsystem:** SEN0325 microphone array and Raspberry Pi Pico  
**Milestone:** Audible-beacon bench prototype; desktop v0.7 / Pico firmware v0.5

## Summary

This week, we established and tested the acoustic sensing path from the SEN0325 6+1 microphone array through the Raspberry Pi Pico to a Windows radar-style direction display. We moved from basic microphone-level tests and unstable single-tone phase estimates to a known coded audible beacon with multi-microphone direction estimation. The audible prototype is ready for further controlled testing; complete robot following and reliable inaudible operation have not been demonstrated.

## Work completed

- Connected the array to the Pico and implemented seven-channel synchronous 48 kHz acquisition using PIO and DMA.
- Implemented USB burst transfer with length, sequence and CRC32 checks, plus dropped-block and RX-stall reporting. Preserved a RAM-only loading workflow.
- Generated transferable phone beacon WAV files and added target-band code matching to reject signals that do not match the selected beacon.
- Added multi-pair SRP-PHAT direction estimation for the audible beacon, consistency checks, temporal filtering, and front-reference/mirror controls.
- Built a simplified 2D radar-style interface with independent receiver and sound-playback switches, seven-channel diagnostics, and distance-tagged trial recording.
- Reduced inter-capture waiting and improved visual refresh. The controlled live loop-timing benchmark increased from 2.92 to 4.57 Hz (about 56.6%); the display timer targets about 30 frames/s.
- Prepared an English interface, project README, organized folders, selected validation evidence and an English/bilingual weekly handoff package.

## Results and evidence

| Evaluation | Result | Scope |
| --- | --- | --- |
| Stationary audible-beacon bench trial | 18/18 evaluated stable playback windows had accepted bearings; 0/6 evaluated off windows did | Computer speaker; true angle and distance were not measured. |
| Unrelated 1 kHz tone | 0/19 evaluated tone-on windows matched the code or gave a valid bearing | One interference case, not a general rejection guarantee. |
| Live timing comparison | Median loop interval decreased from 343 to 219 ms; zero reported drops/RX stalls | No beacon playback; timing/integrity only. |
| Synthetic filter-response comparison | 0°→45° settling within ±5° improved from 1.0 to 0.4 s at the same 5 Hz input rate | Generated samples; not a physical tracking response measurement. |
| High-frequency experiment | Code matched in 19/19 evaluated playback windows, but 0/19 valid directions | Inaudible direction finding remains unsuccessful. |

The user reported that the audible version worked better on the intended Samsung S25 Ultra, while the inaudible version did not work. This feedback has not yet been converted into a controlled distance/angle acceptance test. Detailed reports are included under `reports/validation/`.

## Challenges and current limits

Single-tone phase estimates were often inconsistent, particularly as distance and reflections increased. Coded detection and multi-pair processing provide a better test baseline, but long-range robustness and real angular accuracy remain unverified. Direction is currently computed on the Windows host. The Pico/ESP32 interface, distance-radar alignment and motor-control loop have not been integrated. The radar-style rings indicate no measured range.

## Next steps

1. Measure bearing error and valid-output rate at marked angles and distances with the S25 Ultra, including trials beyond 1 m.
2. Calibrate orientation/timing and test reflections, unrelated audio and source movement.
3. Agree with the ESP32 team on bearing, validity, quality and timeout fields, then integrate the radar/steering loop.
4. Continue high-frequency work separately after the audible baseline is characterized.

## Short update for a meeting

We completed a working bench prototype for our SEN0325/Pico acoustic subsystem. It captures seven microphone channels, identifies a coded audible phone beacon, and displays an estimated bearing on a simplified radar-style interface. We also added packet-integrity checks, diagnostic logging and independent playback controls, and improved the measured acquisition-loop rate from about 2.9 to 4.6 Hz. The next priority is controlled angle-and-distance testing and the ESP32 handoff. Inaudible localization and complete vehicle following are still open.


---

# EE475 周报 — 声学定位子系统

**项目：** Tagalong 跟随机器人  
**截至日期：** 2026 年 10 月 17 日  
**负责部分：** SEN0325 麦克风阵列与 Raspberry Pi Pico  
**本周里程碑：** 可听编码信标台架原型；桌面软件 v0.7 / Pico 固件 v0.5

## 本周概述

本周搭建并测试了 SEN0325 6+1 麦克风阵列、Pico 与 Windows 平面雷达式方向显示之间的声学采集链路。测试由最初的麦克风音量检查和不稳定的单频相位估计，推进到已知编码可听信标识别与多麦克风方向估计。目前可听版本可以继续做受控测试，但尚未证明整车跟随和可靠的不可听定位。

## 已完成工作

- 完成阵列与 Pico 接线，使用 PIO 和 DMA 实现七通道 48 kHz 同步采样。
- 实现 USB 分段音频传输、长度/序号/CRC32 校验，以及丢块和 RX 停顿监测；保留只加载到 RAM 的测试方式。
- 制作可转到手机播放的 WAV 信标，加入目标频带内的编码匹配，拒绝不符合所选编码的信号。
- 为可听信标加入多麦克风对 SRP-PHAT 方位估计、一致性判断、时间滤波和前方零点/镜像设置。
- 制作简化的二维雷达式界面，将接收检测与电脑播放独立控制，增加七通道诊断和带手动距离标签的测试记录。
- 缩短采集间隔并提高画面刷新。受控实机时序对比中，检测循环中位速率从 2.92 提升到 4.57 Hz，约提高 56.6%；界面定时器目标约为每秒 30 帧。
- 完成英文界面、README、项目分类、测试证据整理，以及英文和中英文周报交付。

## 测试结果与证据

| 测试 | 结果 | 适用范围 |
| --- | --- | --- |
| 静止可听信标台架测试 | 播放稳定期的 18/18 个评估窗口输出有效方位；停止后的 6 个评估窗口均无有效方位 | 电脑扬声器；没有测量真实角度和距离。 |
| 非目标 1 kHz 音调 | 播放期的 19 个评估窗口均未匹配编码，也未输出有效方位 | 只证明这一类干扰测试通过，不代表全面抗干扰。 |
| 实机时序对比 | 循环中位间隔从 343 降至 219 ms，两阶段报告的丢块和 RX 停顿均为零 | 未播放信标，仅验证时序和传输状态。 |
| 模拟滤波响应对比 | 同样以 5 Hz 输入时，0°→45° 阶跃稳定到 ±5° 的时间从 1.0 降至 0.4 秒 | 合成样本，不能当作手机实际跟踪响应。 |
| 高频实验 | 19/19 个播放期评估窗口识别到编码，但 0/19 输出有效方向 | 不可听版本的可靠定位尚未成功。 |

用户反馈：计划使用的 Samsung S25 Ultra 上，可听版本可用，不可听版本未成功。这是定性反馈，尚未形成有真实角度和距离记录的受控验收。详细原始报告保存在 `reports/validation/`。

## 遇到的问题与当前限制

单频相位估计经常不一致，距离增加和环境反射会加重问题。编码识别和多麦克风对处理提供了更好的测试基础，但远距离稳定性和实际角度精度仍未验证。目前方位计算运行在 Windows 电脑上，Pico/ESP32 通信、距离雷达对准与电机闭环尚未接通。雷达式显示的圆环不代表测得的距离。

## 下一步

1. 用 S25 Ultra 在已标记角度和已测距离下记录误差与有效输出率，包含 1 m 以外测试。
2. 校准物理方向与通道时序，测试反射、无关声音和声源移动。
3. 与 ESP32 部分约定方位、有效标志、质量和超时字段，再接距离雷达与转向控制。
4. 可听基线得到量化后，再独立推进高频不可听方案。

## 会议口头汇报简版

本周完成了 SEN0325/Pico 声学子系统的可运行台架原型，实现七通道采音、可听编码信标识别和二维雷达式方位显示，并加入数据校验、诊断日志和独立播放控制。实测采集循环速率从约 2.9 提升到 4.6 Hz。接下来重点做有真实角度和距离记录的测试，并与 ESP32 对接。目前还不能宣称不可听定位和整车跟随已经完成。
