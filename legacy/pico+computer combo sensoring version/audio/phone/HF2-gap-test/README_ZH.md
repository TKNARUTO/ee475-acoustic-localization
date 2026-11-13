# 匹配的 HF2 gap 手机音频

使用 `01_LOCATE_18-22kHz_43ms-gap.wav` 或对应 MP3。这就是保留组合的默认 coded-gap 信号。采样率 48 kHz，仅右声道；每周期 4096 点，2048 点发声、2048 点静音，约 42.67 ms＋42.67 ms。不要剪掉静音。电脑选 Gap test／18–22 kHz，再点 Start Scan。比较测试优先 WAV，并记录手机位置、音量。高频输出和可听性取决于手机及听者，不保证完全不可听或固定距离。

平台与工具：电脑端使用 Windows 10/11、Python 3.12+（含 Tcl/Tk）；Pico 通过 USB 采集。手机播放器需 Android 8.0/API 26 或以上。运行旧固件不需要编译器；工具版本及限制见[平台说明](../../../PLATFORM_ZH.md)。当前独立 Pico 程序位于模板根目录上两级的 `pico-standalone/`，不包含在本 ZIP 内。
