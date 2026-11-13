# 保留的采集固件与电脑接收器

本基线由 Windows Python 程序计算方向，Pico 只提供同步 USB 采集。使用模板根目录的启动／更新入口；新独立监视器占用同一串口时不要启动旧接收器。

随包固件是仅在 RAM 运行的 v0.6-RX2，断电后需重载。相邻 main.c／CMakeLists.txt／link_frame.h 是 v0.8-BRIDGE 开发源码，尚未确认能匹配重建 v0.6。bridge_config.json 保持关闭。见[固件来源](firmware/README_ZH.md)和[完整模板说明](../README_ZH.md)。

平台与工具：电脑端使用 Windows 10/11、Python 3.12+（含 Tcl/Tk）；Pico 通过 USB 采集。手机播放器需 Android 8.0/API 26 或以上。运行旧固件不需要编译器；工具版本及限制见[平台说明](../PLATFORM_ZH.md)。当前独立 Pico 程序位于模板根目录上两级的 `pico-standalone/`，不包含在本 ZIP 内。
