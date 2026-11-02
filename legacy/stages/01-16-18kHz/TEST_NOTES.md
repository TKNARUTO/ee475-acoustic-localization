# HF1 phone test sheet / 手机测试记录

**Status: awaiting user measurements. Do not prefill results as passing.**

Record once per test session: date/time, room, phone/player, media volume, player effects, speaker orientation, source/array height, array orientation and any nearby equipment. Keep these fixed while changing distance. Test one source at a time.

## Level test / 强度

Play each TONE file in a loop. Select Start Scan and read the corresponding Tone levels value. Record roughly ten seconds, then pause playback and note the background. These files do not produce a localization arrow.

| File / Hz | Volume | Distance m | Background dBFS | Playing median dBFS | Notes |
| --- | --- | --- | --- | --- | --- |
| 1,000 | | 0.5 / 1 / 1.5 | | | |
| 16,000 | | 0.5 / 1 / 1.5 | | | |
| 17,000 | | 0.5 / 1 / 1.5 | | | |
| 17,500 | | 0.5 / 1 / 1.5 | | | |
| 18,000 | | 0.5 / 1 / 1.5 | | | |

Use separate rows or copies for each distance. If playing and background levels are almost equal, report that; do not interpret the background as a measured beacon. Equal digital file RMS does not mean equal acoustic phone output. Differences across frequencies include both speaker and microphone responses and the room.

## Direction test / 方向

Use 01_LOCATE_16-18kHz.mp3 with 16–18 kHz selected; use 02_LOCATE_Audible.mp3 with Audible beacon. Start at 0.5 m and set front with the source in front. Keep the array fixed, use measured source positions, and record each trial in Advanced > Record 10 s. Enter the measured distance before recording.

| File/profile | Volume | Distance m | True bearing ° | Code hits /7 | Valid windows/total | Bearing range/error | Saved JSON |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HF1 | | 0.5 | 0 / 45 / 90 | | | | |
| HF1 | | 1.0 | 0 / 45 / 90 | | | | |
| HF1 | | 1.5 | 0 / 45 / 90 | | | | |
| Audible | | same positions | | | | | |

A stable arrow alone is not proof of angle accuracy. Enter the actual marked source angle and compare it with the displayed bearing. Files use different digital levels, so the audible/high-band comparison is a practical beacon comparison, not a calibrated hardware frequency-response test.

## How to report a problem / 如何反馈

- No rise above background: report frequency, volume, distance and speaker orientation.
- Signal rises but Code remains below 4/7: report file/profile pair and save a trial.
- Code ≥4/7 but arrow disappears: report the on-screen reason and save a trial; inspect delay/geometry consistency next.
- Arrow points the wrong way: distinguish reversed left/right, a constant angular offset and random jumps. Include actual source angle.

中文：先比较暂停时的背景值，再记录播放值。测试期间不要变音量或转手机。纯音只看电平；定位必须用编码音。把距离、文件名和保存的 JSON 一起交回来，下一阶段再针对结果调整。
