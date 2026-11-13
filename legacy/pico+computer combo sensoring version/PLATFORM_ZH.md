# 平台与工具要求

这是旧的**Windows 电脑运算＋Pico 采集**组合。方向由电脑计算，并非当前的 Pico 独立定位固件。

| 用途 | 要求或记录版本 |
|---|---|
| 接收软件 | Windows 10/11；Python 3.12+，安装 Tcl/Tk |
| Python 运行依赖 | numpy 2.5.4、pyserial 3.5、imageio-ffmpeg 0.6.0；保留的 requirements 文件已固定版本 |
| 采集板 | Raspberry Pi Pico / RP2040；USB 数据线；随包 v0.6-RX2 RAM UF2 |
| 手机 | Beacon Loop 1.2，版本号 3；最低 Android API 26，目标 API 35 |
| 可选复位／加载工具 | 本机记录 picotool 2.3.1；通过 BOOTSEL 磁盘加载不需要它 |
| 2026 年 11 月 12 日开发环境记录 | Pico SDK 2.3.1；Arm GNU Toolchain 14.2.Rel1 / GCC 14.2.1；CMake 4.4.4；Ninja 1.13.2.git.kitware.jobserver-pipe-1 |

以上是本机开发工具版本，**不能证明可以复现随包 v0.6 固件**。相邻 C 源码属于 v0.8-BRIDGE，尚未确认与 v0.6 二进制完全匹配的源码快照。ZIP 不附带 SDK、Python、JDK、Android 编译工具或签名密钥；使用本模板 Setup-Windows.ps1 安装固定的运行依赖。精简归档不包含 Android 源码。

Pico 的 RAM 程序断电即消失，需要重新加载。不同 Windows 版本、新电脑驱动、S25 Ultra 权限和播放表现、实际角度精度都需要实测，离线打包检查不能替代。
