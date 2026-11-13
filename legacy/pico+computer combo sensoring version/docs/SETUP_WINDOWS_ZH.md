# Windows 安装

安装带 Tcl/Tk 的 Python 3.12+，从模板根目录执行：
```powershell
powershell -ExecutionPolicy Bypass -File .\Setup-Windows.ps1 -PythonExe 'C:\Path\To\Python312\python.exe'
```
脚本创建 `.venv`，安装 `SEN0325-Pico-Setup/requirements.txt` 的固定依赖并检查 Python 源码；`-WithPlots` 加装可选绘图依赖。安装依赖可能需要联网。

新电脑应使用本地 `.venv`。保留的启动器也支持 `EE475_PYTHON` 和原维护者的运行环境回退路径，但后者不是可移植要求。`Update.cmd` 只检查并重启本地源码。

使用 USB 数据线；板上运行其他固件时，按住 BOOTSEL 接入。启动器通过 RPI-RP2 复制仅写 SRAM 的 v0.6 固件，这种磁盘加载不需要 picotool。RAM 断电丢失；可选 picotool 回退通过 `EE475_PICOTOOL` 指定。原 Build/Load/Monitor 脚本只是维护者参考，正常使用不需要它们。不能把相邻 v0.8 源码当作已确认的 v0.6 重建来源。

```powershell
.\.venv\Scripts\python.exe .\tools\verify_handoff.py --output-dir C:\Path\To\ComboChecks
```
验证输出放到模板外。硬件测试应独占串口；本次文书更新没有安装新电脑驱动或配置新运行环境。

平台与工具：电脑端使用 Windows 10/11、Python 3.12+（含 Tcl/Tk）；Pico 通过 USB 采集。手机播放器需 Android 8.0/API 26 或以上。运行旧固件不需要编译器；工具版本及限制见[平台说明](../PLATFORM_ZH.md)。当前独立 Pico 程序位于模板根目录上两级的 `pico-standalone/`，不包含在本 ZIP 内。
