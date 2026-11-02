EE475 HF2 - 20 kHz CENTER / 19-21 kHz BAND (2026-10-22)

Phone playback only. The desktop application never plays these files.

01_LOCATE_20kHz_19-21kHz.mp3
  Coded localization beacon. Select "20 kHz beacon | 19-21 kHz", then Start Scan.
  Loop the file on the phone. Use Set Front after a stable direction appears.

11_TONE_19000Hz_level-only.mp3
12_TONE_19500Hz_level-only.mp3
13_TONE_20000Hz_level-only.mp3
14_TONE_20500Hz_level-only.mp3
15_TONE_21000Hz_level-only.mp3
  Equal digital RMS (-20 dBFS), 20 seconds each. Frequency-level comparison only.
  These are pure tones and DO NOT produce a localization arrow.

All files: 48 kHz MP3, highest-quality VBR, left silent/right active. Each file
was decoded and checked after encoding. Fixed-rate 320 kbps encoding attenuated
some frequencies in this band during testing, so the checked VBR files are used.

Start around 0.5 m. Keep phone volume, speaker orientation and height fixed,
then compare 1 m and 1.5 m. Compare paused background with the playing level.
Do not cover the active phone speaker. Avoid EQ, normalization and crossfade.
Phone player speaker routing varies. Use one sound source for localization.

The UI shows actual microphone spectrum and sampled waveform independently
of beacon recognition. 19-21 kHz is shaded. A spectrum rise proves received
energy; code hits prove a reference match; an arrow also requires consistent
multi-microphone timing. These are different checks.

20 kHz does not guarantee stronger penetration, longer range or inaudibility.
Speaker directivity is a physical property; a file cannot synthesize a narrow
acoustic beam from one phone speaker. These assets prioritize a single source,
known code and useful RMS level without clipping. Physical range testing is open.

中文：01 用于测方向，11-15 纯音只看强度，不出箭头正常。
手机单曲循环，电脑只扫描。先 0.5 米，再同音量、同朝向测 1 米、1.5 米。
可先看右侧频谱 19-21 kHz 是否抬升，再看 Code 命中和方向。
用 Import Beacon 可以导入兼容的本地 MP3/WAV 作为检测参考；要在手机上
播放同一个文件。当前支持 48 kHz 下每 4096 点重复的宽带编码信标。
普通音乐、语音、任意 chirp 和纯音不能直接作为当前定位参考。
