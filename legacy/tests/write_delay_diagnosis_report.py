"""Write a report from frozen evidence; do not change the detector or firmware."""
from pathlib import Path
from datetime import datetime
import json
import shutil

PROJECT=Path(__file__).resolve().parents[1]
DEST=PROJECT/'reports/delay-diagnosis-2026-10-22'
e=json.loads((DEST/'diagnostic-evidence.json').read_text(encoding='utf-8'))
before,guarded,smoke=e['sessions']
errors=json.loads((DEST/'packet-error-context.json').read_text(encoding='utf-8'))
def pct(n,d):return f'{100*n/d:.1f}%' if d else 'N/A'

report=f'''# 20 kHz 延迟与方向中断诊断报告

记录日期：{datetime.now().astimezone().isoformat(timespec='seconds')}

本次只定位故障环节并保留证据，不继续实施新的定位算法修复。按用户上一条要求，源码已撤销新增的大角度跳变限制、双估计硬拦截，并恢复原来的两次候选确认。仍保留原有数据完整性检查和时延几何检查。运行中程序与磁盘源码的区别见文末。

## 1. 目前已经定位到哪里

有两条不同的问题链，不能统称为“delay 导致断联”。

**常见的箭头消失：发生在电脑端的多麦克风相对时延估计／几何拟合阶段。** 音频已经成功到达电脑，编码也被多路麦克风识别，但各对麦克风算出的时差不能共同解释为一个声源方向。程序因此返回 `group_delay_inconsistent`，界面清掉箭头。这个标签表示“麦克风间时差不一致”，不是 USB 已经断开。

**少见但明显的约 8.5 秒中断：发生在原始音频包的接收／长度与 CRC 校验边界。** 日志有两次 `Raw packet length/CRC check failed`，随后接收会话退出并重试。它们是真实的数据流程中断，需要独立排查。

**正常工作时的刷新延迟：主要耗在采集、等待和传输的合并阶段。** 一次数据处理循环通常约 0.21–0.22 秒，强编码信号的 DSP 计算中位数约 15 毫秒。现有日志还不能把设备采样等待和 USB 负载传输分别计时，因此不能把这约 200 毫秒全部归到 USB。

## 2. 分段检查结果

| 环节 | 已有证据 | 本次判断 |
| --- | --- | --- |
| 手机音频 → SEN0325 | 存在 7/7 通道编码命中、PNR 34.59 dB 的实际记录 | 能收到并识别指定高频音；“完全听不见”不是这些失败窗口的原因 |
| Pico I2S/PIO/DMA 采集 | 检查会话内，包头 `dropped` 最大 0、`rx_stall` 最大 0，序号没有倒退 | 没发现所记录采集块内的 DMA 丢块／PIO RX 停顿；这不证明所有通道的物理时序已校准 |
| 原始音频包 → 电脑 | 前一会话有 2 次长度/CRC 校验失败 | 此处确实有偶发异常；还不能判定是短包、CRC 不符、固件发送、主机解析还是 USB 物理问题 |
| 已知编码检测 | 前一会话 1,513 个窗口至少 4 路命中；其中 1,076 个为至少 6 路、PNR ≥24 dB | 很多方向失败发生在已经识别编码之后 |
| 麦克风对时差 → 几何方向 | 编码已命中的 1,513 窗口中，919 次报时延不一致，约 {pct(919,1513)} | 这是频繁失去方向的主要已定位环节 |
| 新增的反向规避策略 | 后一会话 409 个编码命中窗口中，236 次被 `estimator_disagreement` 拦截 | 新策略明显降低可用性；源码已经撤销它，不以限制转向代替修复时差估计 |
| 界面显示 | 无效结果会立即清掉箭头；界面刷新与采集循环分开 | “没有箭头”经常是上游给了无效方向，不代表界面停止接收 |

两段手机播放记录不是同位置、同音量的受控实验。表内数字只用于定位失败发生在哪一层，不能用来宣称新旧版本的角度精度或距离性能。

## 3. 频繁的时延拟合失败：具体证据

示例时间：**2026-10-22 17:52:19.206（本机时区）**。

| 字段 | 记录值 | 说明 |
| --- | --- | --- |
| 编码命中 | 7/7 | 全部七路都识别到所选编码 |
| 编码 PNR | 34.59 dB | 属于较强的编码匹配 |
| 19–21 kHz 数字电平 | −49.5 dBFS | 接收到的频带能量；不是校准声压 |
| 麦克风对 | 20 | 已有足够的成对信息进入拟合 |
| 成对相干性中位数 | 0.958 | 相干性高也不能保证几何一致 |
| 保留对的时差残差 RMS | 2.3869 采样点 | 超过当前 1 点门槛 |
| 全部对的残差 RMS | 2.8083 采样点 | 超过当前 1.5 点门槛 |
| 水平投影长度 | 0.5236 | 在现有 0.25–1.3 范围内 |
| 拒绝原因 | `geometry_mismatch` | 各对时差不能共同解释当前阵列模型 |

48 kHz 下，1 个采样点约 20.83 微秒，相当于约 7.15 毫米声程。这里的“delay”是这种通道间微小时差；它与一次界面更新花了多少毫秒不是同一个量。

在前一会话的 919 次时延不一致记录里，900 次同时超过保留对残差和全部对残差门槛；71 次还超出水平投影范围，2 次属于时差对不足。这些分类可重叠，不能相加作为总数。故障主要出现在**已获得多个时差候选、随后无法满足几何一致性**，不是始终没有检测到编码。

目前可以定位到这一软件计算环节，但尚不能唯一确定更深的物理原因。需要区分的候选包括：近距离反射使各通道偏向不同到达路径、19–21 kHz 内各通道频响／群延迟不一致、有效频带变窄、实际通道顺序或几何与配置不符。现有历史日志没有相应的 20 kHz 原始波形和同步已知摆位，不能把这些推测写成已证实结论。

## 4. 两次约 8.5 秒中断：具体证据

| 上一个有效采集结果时间 | 恢复结果时间 | 结果间隔 |
| --- | --- | --- |
| 17:59:25.599 | 17:59:34.156 | 8.562 s |
| 18:00:03.632 | 18:00:12.127 | 8.515 s |

两处均伴随 `Raw packet length/CRC check failed; bearing suppressed.`。这是结果之间的实际间隔，不是单独测得的 USB 传输耗时。

接收代码把“长度不符”和“CRC 不符”合并为一条错误；当前日志没有保存失败时的实际字节数、计算出的 CRC 或分段接收时间。异常后退出串口会话，并等待 3 秒再试；读包本身还有截止时间，重新启动采集还有预热。因此会放大成数秒没有新方向。

本次不能断言是坏 USB 线或固件错误，也不能继续说传输完全没有问题。定位结果是：**原始音频包接收／校验层存在两次可复现到日志时间点的异常，其详细成因仍待分段计时。**

## 5. 正常循环究竟慢在哪里

以下为前一会话的正常循环统计；大于等于 450 ms 的启动／重启周期单独排除。

| 指标 | 中位数 | P95 | 边界 |
| --- | --- | --- | --- |
| 一次 `RECORD` 到 DSP 完成 | {before['capture_cycle_steady_ms']['median']:.2f} ms | {before['capture_cycle_steady_ms']['p95']:.2f} ms | 包含设备采集、接收、校验和 DSP |
| 强编码窗口的同一循环 | {before['strong_code_cycle_steady_ms']['median']:.2f} ms | {before['strong_code_cycle_steady_ms']['p95']:.2f} ms | 至少 6 路命中且 PNR ≥24 dB |
| 强编码窗口的 DSP | {before['dsp_ms_strong_code']['median']:.2f} ms | {before['dsp_ms_strong_code']['p95']:.2f} ms | 不含 USB 读包；也不含界面绘制 |
| DSP 之前的设备／接收合并段 | {before['device_io_wait_before_dsp_ms']['median']:.2f} ms | {before['device_io_wait_before_dsp_ms']['p95']:.2f} ms | 每窗口循环时长减 DSP；不能再直接拆成 USB 与采样两项 |
| 连续估计结果间隔 | {before['steady_estimate_interval_ms']['median']:.2f} ms | {before['steady_estimate_interval_ms']['p95']:.2f} ms | 约 {1000/before['steady_estimate_interval_ms']['median']:.2f} 次/秒；不是画面帧率 |

4096 点／48 kHz 的采样时间固定为 **85.33 ms**。Pico 每次原始包为 **57,344 字节**。首次启动原始采集会设置 **500 ms 预热**；前一会话记录到的启动／重启循环为 763.05、738.87、743.80 ms。正常连续 `RECORD` 不会每包重复这 500 ms 预热。

设备 `process_us` 是每个 1024 帧缓冲的最大处理时间，不是整包总耗时，不能当作端到端延迟。串口 `timeout=0.15` 也不等于每个成功读取都会固定额外睡 150 ms。要单独定位那约 200 ms 合并段，必须增加边界时间戳；本阶段没有改这些实现。

原有两次候选确认、2–3 块历史和显示平滑还会增加从声源变化到稳定箭头的等待。更明显的“停顿”则来自大量方向拒绝和上述两次接收异常。现有日志不能给出精确的“手机发声到屏幕出现正确箭头”的端到端值。

## 6. 为什么上一版几乎不出箭头

有新拦截策略的会话中，409 个编码命中窗口的结果是：

- 236 次双估计不一致，约 {pct(236,409)}；
- 81 次还在等待连续方向确认，约 {pct(81,409)}；
- 68 次原有时延拟合不一致，约 {pct(68,409)}；
- 24 次输出有效方向，约 {pct(24,409)}。

该快照里没有 `direction_jump_rejected` 事件。因此这次“几乎没有箭头”的主要新增拦截来自**双估计一致性硬要求**，不能把全部责任都归到大角度跳变限幅。用户提出的不应强制约束真实转向也成立；两个新增硬限制都已从源码撤销，候选确认恢复两次。

这段记录与前一会话播放条件不同，不以有效率差值评价精度。

## 7. 反向跳变与校准

用户确认是在静止或缓慢移动时突然指向反面。前一会话的连续有效方向中也找到跨输出空档的大幅变化，例如 17:52:27.912 → 17:52:30.004，相隔 2.094 秒，新旧原始方向变化 124.16°；还有间隔约 5 秒和 10 秒的类似记录。它们支持“输出中断后重新得到不同方向”的现象。没有同步标定的真实角度，日志不能单独证明每一帧到底错了多少度。

当前几何配置还没有保存 Set Front，且物理朝向标记未验证。这影响 0°／前后标签的含义，但**不足以解释用户确认的突然反向跳变**，不能把这次问题简单归为没校准，更不能整体翻转 180°。

## 8. 下一步只建议这些测量，尚未实施

1. **先拆开接收计时和错误原因。** 记录发出 RECORD、收到包头、负载接收结束、校验结束、DSP 开始／结束、进入界面队列和实际绘制的时间。错误时分别记录实际长度／预期长度、收到的 CRC／计算的 CRC、序号与尾标记。保持声学算法和阈值不变。
2. **再对同一段 20 kHz 原始数据做离线分析。** 在固定、已知角度的位置保存编码音播放时的原始七路采样，检查各对时差、三角闭合关系、频段分布、中心麦与环形麦差异，区分通道偏移和反射影响。不要只拿最终角度做判断。
3. 同一数据分别查看主时差拟合和共同到达峰候选，解释它们为什么会冲突；等报告里的缺失证据补齐，再决定改采集、收包、群延迟校准还是拟合方法。

以上是后续测量计划，**没有在本轮继续改算法或固件**。本次交付到诊断报告为止。

## 9. 证据、版本与可重复性

- `diagnostic-evidence.json`：完整统计、源码 SHA256、阈值触发与日志快照哈希。
- `packet-error-context.json`：两次异常前后时间和间隔。
- 本目录三份 `launcher-*.txt`：本次分析时冻结的日志，包含一份 Pico／界面／导入流程检查记录。打开中的日志末尾不完整 JSON 行会跳过并计数。
- `tests/diagnose_delay_pipeline.py`：只读分析脚本。重新运行会生成新的快照，不能拿不同快照数字直接比较。
- `highband_dsp.py` 磁盘源码已撤销新增角度跳变和双估计硬拦截；拍取证据时运行中的旧进程仍有拦截，因此会话按实际输出原因分类。报告生成后只做已授权的版本回退加载，不启动新的修复实验。

## English summary

The frequent loss of bearing is localized to host-side microphone-pair delay estimation and geometric consistency fitting, after successful code detection. In one session, 919 of 1,513 code-matched windows were rejected at this stage. A representative failure had seven code hits and 34.59 dB PNR but pair-delay residuals above the geometry gates.

There is a separate transport/packet-validation issue: two length/CRC errors were followed by approximately 8.56 s and 8.52 s gaps between results. Existing logs cannot distinguish short payloads from CRC mismatches. Normal request-to-DSP cycles were roughly 215 ms, with strong-signal DSP around 15 ms; acquisition and I/O are not separately timestamped.

The added hard dual-estimator gate rejected 236 of 409 code-matched windows in a later, uncontrolled session and was the main new cause of missing arrows. The new angular-jump veto and hard dual-estimator veto have been removed from source at the user's request. Physical causes of inconsistent microphone delays remain unproven; no further algorithm or firmware changes are claimed by this diagnostic report.
'''
(DEST/'DELAY_DIAGNOSIS_ZH.md').write_text(report,encoding='utf-8')
(DEST/'DELAY_DIAGNOSIS.txt').write_text(report,encoding='utf-8')
stage=PROJECT/'stages/02-20kHz';stage.mkdir(exist_ok=True)
(stage/'README.md').write_text('''# HF2 — 20 kHz receiver and diagnostic checkpoint

**22 October 2026 · Default center 20 kHz, coded band 19–21 kHz · Diagnosis delivered; further repair deferred**

The app receives only. Main controls are Start Scan, Import Beacon, Set Front and Advanced. Launch `Start-20kHz.cmd` at the project root. Play `audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3` on the phone. The five TONE files measure received level only and do not produce a bearing.

The direction radar is retained. The second panel shows actual captured microphone spectrum and a sampled waveform, independently of code detection. The shaded band follows the reference. Waveform scale is labeled PCM; spectral levels are digital dBFS/bin, not calibrated sound pressure.

## Import a reference

Select Import Beacon and choose an MP3 or WAV. Analysis runs in the background. The app identifies the occupied band and verifies compatibility before switching the detector. A failed import preserves the previous reference and scan state. The original file is unchanged; a copy, normalized template and manifest are stored under `SEN0325-Pico-Setup/beacon_profiles/<hash>/`. The last imported reference remains available in the selector after restarting; the normal launcher defaults to the 20 kHz preset.

Current import support is deliberately specific: a wide coded reference repeating every 4096 samples (85.333 ms at decoded 48 kHz), at least 1 kHz occupied bandwidth and usable frequencies from 300 Hz to 22 kHz. Pure tones, arbitrary music/voice and nonperiodic chirps are rejected. The same accepted source file must be played on the phone. This is not a universal audio fingerprinting detector.

## Diagnostic checkpoint

Read the [delay diagnosis report](../../reports/delay-diagnosis-2026-10-22/DELAY_DIAGNOSIS_ZH.md). Frequent direction loss occurs after code detection, at the relative-delay/geometric fit. Two separate packet length/CRC failures also caused about 8.5 s gaps. The physical root cause of inconsistent delays has not yet been isolated.

The experimental hard turn/jump veto and hard dual-estimator veto were removed after user feedback. Large real turns are not forbidden. Existing packet integrity, clipping and geometric validity checks remain. No successful physical reversal fix is claimed.

Advanced > Record 10 s saves metrics and a local NPZ of captured samples when a trial completes. Enter the measured distance honestly and record source position, phone volume and file separately. Keep the source fixed for an initial known-angle trial. A missing arrow is not a measured wrong angle; an accepted arrow is not proof of accuracy.

## Evidence and status

`model-validation.json`, `mp3-validation.json`, `import-validation.json`, `english-ui-validation.json` and the archived hardware check document their own conditions. Simulated accuracy and codec checks do not establish phone range. `direction-guard-validation.json` is historical evidence for the rejected policy, not a current feature guarantee.

The original 17 October release and the HF1 checkpoint are retained. GPIO wiring, Pico firmware v0.5 and raw packet format are unchanged. Next work should add per-stage timing and failed-packet detail before altering the sound-localization algorithm.

中文：目前先停在诊断报告，尚未解决实测的反向／时差不一致问题。默认 20 kHz，手机播放，电脑只接收。导入功能支持兼容的周期编码音，不能把任意音乐或纯音直接当定位信标。
''',encoding='utf-8')
(stage/'PROGRESS_NOTES.md').write_text('''# HF2 progress notes / 阶段汇报

本阶段完成了 20 kHz 中心（19–21 kHz）预设、经过解码检查的手机 MP3、频谱与采样波形显示，以及兼容 MP3/WAV 编码信标的导入。实际 Pico 导入流程检查采集了 38 个七路数据块，界面与导入流程检查通过；没有由电脑播放声音。

手机实测发现时差拟合不一致和突然反向，尚未解决。后来加的双估计硬拦截大幅减少了箭头输出；用户要求撤销，相关源码已回退。不能把“少显示箭头”写成方向算法已修好。

完整日志又发现两次原始包长度/CRC 校验错误，分别造成约 8.56 秒和 8.52 秒无新结果。此前仅凭 dropped=0 就说传输没有问题，结论过宽，已在诊断报告中更正。

当前检查点：诊断报告已交付，后续先补分段计时和错误详情，再基于同一段原始七路数据定位问题。没有在本轮继续实施新的修复。

See ../../reports/delay-diagnosis-2026-10-22/DELAY_DIAGNOSIS_ZH.md for evidence, limits and the proposed measurement order.
''',encoding='utf-8')
(stage/'CHANGE_DETAILS.md').write_text('''# HF2 implementation and current limits

- `beacon_dsp.py`: 20 kHz center / 19–21 kHz coded preset and compatible imported references. Known-code matching is required for direction; pure tones only show up in the signal view.
- `highband_dsp.py`, `arrival_dsp.py`: pair-delay fit and strong-code arrival-consensus fallback. Physical multipath/group-delay consistency remains unresolved. The experimental hard angular-jump veto, hard dual-estimator veto and three-candidate requirement were removed; baseline two-candidate confirmation is restored.
- `signal_scope.py`: Hann-window spectrum power averaged across seven captured channels; waveform from the labeled strongest-RMS channel. These display captured data before beacon filtering. No SPL or distance calibration is implied.
- `beacon_importer.py`: local WAV/MP3 decoding, occupied-band and periodicity validation, source-preserving local cache, manifest and normalized template. Compatibility requires a 4096-sample repeating wide code at 48 kHz. `imageio-ffmpeg==0.6.0` is added to runtime dependencies for import; it decodes audio and never opens an output device.
- `app_controls.py`, `sen0325_simple_view.py`: receiver-only scan controls, Import Beacon, spectrum/waveform, calibration, diagnostics and trial capture. Queued results from a previous reference are discarded after switching. The uncalibrated radar labels use an array reference rather than claiming physical front.
- `sen0325_launcher.py`: explicit profile centers, unchanged packet validation, a bounded in-memory raw history and completed-trial NPZ export. Stable multi-sample Set Front is a reference operation; it is not an angular motion limit.
- `audio/phone/HF2-20kHz/`: one coded localization MP3 and five equal-RMS pure probes at 19/19.5/20/20.5/21 kHz. Highest-quality VBR with an explicit 22 kHz cutoff passed decode checks; tested fixed 320 kbps encoding attenuated some upper-band tones. The shipped VBR assets needed no level compensation. Left is silent and right is active. Lossless reference: `audio/phone/coded_20khz_19_21_right.wav`.

A single active phone channel avoids deliberately generating two independent speaker sources, but a file cannot impose a guaranteed acoustic beam or stronger penetration. Directivity and high-frequency absorption depend on the transducer and propagation: [Genelec directivity explanation](https://www.genelec.com/key-technologies/directivity-control-waveguide-technology), [DPA microphone specification discussion](https://www.dpamicrophones.com/mic-university/technology/how-to-read-microphone-specifications/). Actual phone speaker routing and range remain experimental.

The diagnosis report is the current checkpoint. No further algorithm/firmware repair is claimed or performed after the request to report first. The GPIO table in the project README remains authoritative and unchanged.
''',encoding='utf-8')

root=PROJECT/'README.md'
content=root.read_text(encoding='utf-8')
head=content.index('## SEN0325-to-Pico GPIO wiring')
tail=content[head:]
intro='''# Tagalong | Acoustic Localization Prototype

**EE475 · Current checkpoint: HF2, 22 October 2026 · Pico firmware v0.5**

Current status: [20 kHz stage README](stages/02-20kHz/README.md), [progress notes](stages/02-20kHz/PROGRESS_NOTES.md), [change details](stages/02-20kHz/CHANGE_DETAILS.md). Read the [delay diagnosis](reports/delay-diagnosis-2026-10-22/DELAY_DIAGNOSIS_ZH.md) before further changes. Physical direction stability and range remain unresolved; work is paused at the requested diagnostic checkpoint.

A phone plays a coded beacon. A SEN0325 6+1 array and Raspberry Pi Pico capture synchronous audio, and this Windows receiver estimates bearing. The radar rings do not measure distance. ESP32, distance radar and motor integration remain future work.

## Quick start on the configured Windows computer

1. Keep the GPIO wiring below and connect one Pico. Close other serial monitors.
2. Open **Start-20kHz.cmd**. The standard Start-Localizer entry also now defaults to the 20 kHz receiver. Select **Start Scan**; computer playback is not implemented.
3. Loop **audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3** on the phone. The preset uses a 20 kHz center with 19–21 kHz bandwidth. Files 11–15 are pure level probes and do not produce a bearing.
4. Use **Import Beacon** for a compatible local MP3/WAV reference. The app analyzes and validates it before switching; play the same file on the phone. See the stage README for periodic-code restrictions.
5. The second panel shows actual spectrum and sampled waveform, even with no matching beacon. Code hits and valid direction are separate checks.
6. Set Front defines the physical forward reference after stable measurements. Advanced provides reconnect, mirror view, history and measured-distance trials. Completed 10 s trials save both metrics and local raw data for diagnosis.

The original 17 October package and HF1 stage are retained as historical checkpoints. The latest diagnostic report records both frequent geometric-fit rejection and rare packet-validation interruptions. Raising frequency does not establish better range or penetration.

'''
content=intro+tail
content=content.replace('| `stages/01-16-18kHz/` | Current stage README, progress/change notes, test sheet, evidence and pre-stage backup. |',
                        '| `stages/02-20kHz/` | Current stage README, notes, import/codec/UI evidence and diagnostic checkpoint. |\n| `stages/01-16-18kHz/` | Historical HF1 checkpoint, raw phone debugging data and pre-stage backup. |')
content=content.replace('- [User guide](docs/USER_GUIDE.md)','- [Current HF2 operation and limits](stages/02-20kHz/README.md)\n- [Delay diagnosis](reports/delay-diagnosis-2026-10-22/DELAY_DIAGNOSIS_ZH.md)\n- [Earlier user guide](docs/USER_GUIDE.md)')
root.write_text(content,encoding='utf-8')
for target in [Path(r'C:\Users\33296\Documents\Codex\2026-10-08\w\outputs\EE475-README.md'),PROJECT/'releases/Slack-Upload/README.md']:
    shutil.copy2(root,target)
shutil.copy2(DEST/'DELAY_DIAGNOSIS_ZH.md',Path(r'C:\Users\33296\Documents\Codex\2026-10-08\w\outputs\EE475-Delay-Diagnosis-2026-10-22.md'))
print('Diagnostic report and stage notes written:',DEST/'DELAY_DIAGNOSIS_ZH.md')
