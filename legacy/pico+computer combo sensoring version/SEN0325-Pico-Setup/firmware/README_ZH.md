# 保留的 v0.6-RX2 RAM 固件

sen0325_setup-RAM.uf2 与 .elf 是保留的可执行文件对。UF2 SHA-256：`76470847618d44065001eba3615cf49e19e858a27839dd09543700e7d8471151`。

48 kHz、4096 帧、七路有符号 16 位采样，GPIO 与通道顺序保持原样。USB 发送软件 FIFO 为 4096 B，接收 FIFO／传输缓冲区为 512 B，USB 全速包仍为 64 B；CRC32 与 zlib 兼容。UF2 全部载荷指向 SRAM，不写 Flash，断电后需重新加载。

启动器先校验 UF2，再通过 RPI-RP2 BOOTSEL 磁盘或已配置的可选 picotool 加载。上级目录的 main.c／CMakeLists.txt 属于 v0.8-BRIDGE 开发版本；不能声称它们能复现此 v0.6 二进制。不要仅运行 Build.ps1 就覆盖已保留的基线。

平台与工具：电脑端使用 Windows 10/11、Python 3.12+（含 Tcl/Tk）；Pico 通过 USB 采集。手机播放器需 Android 8.0/API 26 或以上。运行旧固件不需要编译器；工具版本及限制见[平台说明](../../PLATFORM_ZH.md)。当前独立 Pico 程序位于模板根目录上两级的 `pico-standalone/`，不包含在本 ZIP 内。
