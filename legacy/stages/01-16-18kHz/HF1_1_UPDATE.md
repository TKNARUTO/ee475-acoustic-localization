# HF1.1 — direction repair and signal scope

The phone beacon was detected on all seven channels, but the pair-delay geometry check rejected most bearings. Strong-code-only arrival consensus now offers a second fit using actual envelope peaks on at least five channels, with retained RMS <=0.9 samples. The original complex-delay gates remain in place. Weak signals do not use this fallback.

Saved 48-block physical replay: 1 accepted bearing before, 5 after. This is still limited availability and has no independently measured angular truth. Generated strong mixed-reflection tests passed at five of six angles; the 45-degree case remained rejected. The original 30-case regression and negative checks passed.

The main window now contains the direction radar plus an actual microphone spectrum and sampled waveform. Spectrum power is averaged over seven channels before code filtering; the waveform shows the labeled strongest-RMS channel. No beacon is needed to update these graphs.

中文：手机高频已经能收到，主要问题是多路时延拟合不一致。强编码情况下增加共同到达峰拟合，原来的弱信号和一致性检查保留。保存的数据回放由 1/48 提高到 5/48，仍需实测，不能说已解决远距离定位。右侧增加实际频谱与波形。

Next user-requested stage: move the beacon to 20 kHz center, 19–21 kHz band; preserve this stage for comparison.
