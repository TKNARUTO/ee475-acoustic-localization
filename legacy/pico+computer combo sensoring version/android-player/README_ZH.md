# 随包手机播放器：Beacon Loop 1.2

安装 `releases/BeaconLoop-1.2.apk`；最低 Android API 26，目标 API 35。使用内置 HF2 gap，或选择兼容的本地音频。Play loop 开始循环，Pause 暂停；音量使用手机媒体音量。基线比较先关闭 Normalize，记录位置、距离和音量。

约 42.67 ms 发声／42.67 ms 静音是原音频设计。精确比较优先 WAV，MP3 编码填充不会自动删除。Normalize 仅在峰值限制下将整体增益最多提高 3 dB，不改变频率、不校准阵列，也不保证更远距离。

1.2 使用原 1.0 的签名，不能直接覆盖另一签名的 1.1；决定替换前保留需要的应用状态。精简模板只含 APK 和文书，不含 Android 源码、SDK/JDK 或密钥。本次没有安装、卸载或修改手机。见[版本记录](CHANGELOG_ZH.md)。

平台与工具：电脑端使用 Windows 10/11、Python 3.12+（含 Tcl/Tk）；Pico 通过 USB 采集。手机播放器需 Android 8.0/API 26 或以上。运行旧固件不需要编译器；工具版本及限制见[平台说明](../PLATFORM_ZH.md)。当前独立 Pico 程序位于模板根目录上两级的 `pico-standalone/`，不包含在本 ZIP 内。
