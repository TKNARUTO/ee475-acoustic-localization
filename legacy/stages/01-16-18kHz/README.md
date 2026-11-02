# HF1 — 16–18 kHz phone test

**22 October 2026 · Stage 1 · Ready for user testing; physical range acceptance pending**

This stage adds a receiver for a known coded beacon in the actual 16–18 kHz band. The desktop application only captures and scans. It has no computer playback control or audio output backend. Play the supplied MP3 files on the Samsung S25 Ultra speaker.

The earlier high-frequency beacon occupied approximately 20–22 kHz. It is a different signal and will not match this receiver. The audible beacon remains available as the baseline.

## Start the test

1. Keep the existing wiring and connect the Pico by USB. Close other serial monitors.
2. Open `Start-16-18kHz.cmd` at the EE475 project root. The receiver starts stopped, with **16-18 kHz beacon (Stage 1)** selected. Select **Start Scan**.
3. Transfer `audio/phone/HF1-MP3/` or `releases/EE475-Phone-MP3-HF1.zip` to the phone.
4. Loop **01_LOCATE_16-18kHz.mp3**, initially about 0.5 m from the array. Keep one phone speaker unobstructed. Use a comfortable volume and keep it fixed throughout the comparison.
5. After a stable arrow appears with the phone physically in front, select **Set Front**. Keep the array fixed while moving the phone left and right.
6. Compare 0.5 m, 1 m and 1.5 m at the same phone volume, height and orientation. These are test distances, not validated operating limits.
7. In **Advanced**, enter the measured distance and select **Record 10 s**. The program saves a `range-test-*.json` file in `SEN0325-Pico-Setup/logs/`. Record the filename, volume and true source angle separately.

Use **02_LOCATE_Audible.mp3** with the **Audible beacon** receiver for an audible baseline. The two coded files use different digital levels, so do not compare their absolute received levels as calibrated frequency response.

## Which file to use

| File | Receiver / purpose | Expected display |
| --- | --- | --- |
| `01_LOCATE_16-18kHz.mp3` | 16–18 kHz coded localization | Code hits; arrow only when the geometry checks pass |
| `02_LOCATE_Audible.mp3` | Audible coded localization, 0.9–3.9 kHz | Baseline code hits and bearing |
| `11_TONE_1000Hz_level-only.mp3` | 1 kHz level reference | Read the 1 kHz tone level |
| `12_TONE_16000Hz_level-only.mp3` | 16 kHz level probe | Read the 16 kHz tone level |
| `13_TONE_17000Hz_level-only.mp3` | 17 kHz level probe | Read the 17 kHz tone level |
| `14_TONE_17500Hz_level-only.mp3` | 17.5 kHz level probe | Read the 17.5 kHz tone level |
| `15_TONE_18000Hz_level-only.mp3` | 18 kHz level probe | Read the 18 kHz tone level |

**TONE files do not contain the localization code. No arrow is expected.** Their digital RMS levels are equal. Use them to compare received strength at different frequencies and distances. Both receiver selections report these five level probes.

All files are actual 48 kHz, 320 kbps MP3s. The left channel is silent; the right carries the signal to reduce interference between two phone speakers. Player routing can vary. Avoid Bluetooth/headphones for this test. Disable player equalization, normalization and crossfade if enabled. The original lossless WAVs remain in `audio/phone/` as references.

## Read the measurements

- **Code: n/7** counts channels that matched the known beacon. Four are required before this stage attempts a direction fit.
- **16–18 kHz level** is median channel energy across that whole band, measured before spectral weighting.
- **Tone levels** are median channel RMS in ±150 Hz windows around 1/16/17/17.5/18 kHz. They update even when no localization code is detected.
- Levels are digital **dBFS**, not calibrated dB SPL. A less negative value means a stronger received signal. Pause phone playback to measure the background; a reading near that background is inconclusive.
- The arrow shows bearing only. The rings do not show range. Set Front changes the zero reference, not microphone timing calibration.
- Display refresh and capture/detection rate are different. This stage does not claim a completed latency improvement.

For example, a tone changing from −60 dBFS at 0.5 m to −70 dBFS at 1 m has dropped by 10 dB in this setup. Compare the same file, source volume and orientation. Changing to a phone speaker may improve the usable signal, but distance attenuation remains physical and must be measured.

## Scope and status

Implemented: band-matched code, lower crest factor within that band, partial spectral whitening, bounded multi-pair delay fitting, conservative direction confirmation, scanner-only UI, frequency probes and MP3 handoff.

Checked: generated-signal regression, negative examples, legacy audible regression, real Pico transport/GUI, MP3 spectrum and code compatibility after decoding. **No phone distance or physical angular-accuracy acceptance has been completed for HF1.** 16–18 kHz is not guaranteed inaudible.

Next changes to latency and longer-range behavior wait for this stage's feedback. See [progress notes](PROGRESS_NOTES.md), [change details](CHANGE_DETAILS.md) and [test sheet](TEST_NOTES.md).

## 中文快速说明

电脑只接收；手机外放单曲循环。测方向先放 `01_LOCATE_16-18kHz.mp3`，软件选 16–18 kHz，然后点 **Start Scan**。先测 0.5 米，稳定后 **Set Front**；保持音量和手机朝向不变，再测 1 米、1.5 米。

11–15 是纯音，只看右侧对应频率的 **Tone levels**，不出箭头正常。暂停播放看一下背景值，数值越不负，接收到的信号越强。测方向必须换回 01 或 02 编码音，并选对应的 Receiver。

这次先完成高频接收这一步。文件检查和 Pico 采集检查已通过，手机远距离是否改善由这次实测确认。
