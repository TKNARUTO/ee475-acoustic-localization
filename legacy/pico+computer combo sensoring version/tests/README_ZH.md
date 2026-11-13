# 离线检查

在模板根目录运行 `python tools/verify_handoff.py --output-dir <模板外目录>`。六组检查覆盖 Python 语法、启动器源码、UF2 仅写 SRAM、只接收控制、数据包异常和 gap 合成模型，不打开串口。务必显式指定模板外输出目录；未改动的历史默认值会在模板内生成阶段目录。

verify_english_ui.py 是可选的断开硬件／模拟 Tk 界面检查，需要桌面会话，不在本次六组复测之内。绘图依赖也是可选。检查不含私有麦克风录音，不能证明实际角度精度、距离或对所有干扰的可靠拒绝。运行日志不属于保存的基线校验内容。

平台与工具：电脑端使用 Windows 10/11、Python 3.12+（含 Tcl/Tk）；Pico 通过 USB 采集。手机播放器需 Android 8.0/API 26 或以上。运行旧固件不需要编译器；工具版本及限制见[平台说明](../PLATFORM_ZH.md)。当前独立 Pico 程序位于模板根目录上两级的 `pico-standalone/`，不包含在本 ZIP 内。
