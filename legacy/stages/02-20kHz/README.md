# HF2 — 20 kHz receiver and diagnostic checkpoint

Historical HF2 receiver checkpoint. The current host packet recovery update is documented in [RX1](../03-packet-timing/README.md); its DSP and phone files remain those described here.

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
