# Windows 安装与入口
使用 Windows PowerShell。安装带 **Tcl/Tk** 的 Python 3.12 以上，在项目根目录运行：
```powershell
.\Setup-Windows.ps1 -PythonExe 'C:\Path\To\Python312\python.exe'
.\Start.cmd
```
安装脚本创建 .venv，安装 requirements.txt，并检查独立监视器。已有环境可设置 EE475_PYTHON 指向 pythonw.exe。本机现有运行环境只是后备选项，别人的电脑不需要使用相同路径。Update.cmd 只重启本地代码；下载源码更新另用 Git。

主要入口只有 Start.cmd 与 Update.cmd；Setup-Windows.ps1 是首次安装辅助脚本。两个启动入口都不烧录、不播放声音。日志只保存在 pico-standalone/logs，不上传。监视器自动识别一块 Pico；遥测应显示 v0.2-link_diag 和 integer_q15_fast。

Pico 使用 Pico SDK 2.3.1、Arm GNU 14.2.Rel1 和 picotool 2.3.1。明确的整数 FFT／FAST 开关和持久 UF2 见 [Pico 说明](../pico-standalone/README_ZH.md)。**不能用 legacy 启动器连接当前独立固件**，旧启动器会装入另一套采集镜像。

ESP32 使用 Arduino IDE 2.3.8／CLI1.4.1、**esp32 by Espressif Systems 3.3.12** 板卡包，板型 **NodeMCU-32S**。详见 [ESP32 安装](../esp32-link/gap_receiver/README_ZH.md)。本机 ESP 是 COM6，Pico 目前 COM8；其他电脑需重新枚举：
```powershell
python -m serial.tools.list_ports -v
arduino-cli board list
```
即使显示通用 USB Serial Port，也可能是正常 ESP 端口。自动识别不了型号时手动选板型即可。一个串口同时只开一个读取程序。BOOTSEL 与普通固件的 USB 枚举可能不同。

有限时间双端采集示例（替换实际端口，输出必须是项目外的新目录）：
```powershell
python pico-standalone/tools/monitor.py --port COM8 --port COM6 --seconds 30 --output C:\BenchResults\trial-new
python pico-standalone/tools/analyze_link_trial.py C:\BenchResults\trial-new --output C:\BenchResults\analysis-new
```
监控器先有界保存启动原始字节，各端清一次输入缓冲，并对齐换行，再开始正式记录。正式阶段不去重。它只是记录遥测，声学方向仍由 Pico 计算。
