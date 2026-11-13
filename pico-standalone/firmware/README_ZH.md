# Pico 持久固件
这是已部署的 Raspberry Pi Pico／RP2040 **v0.2-link_diag** Flash 镜像。UF2 SHA256：**11958e9310926e856f01359c10c4832cffc046cb64a8edebe675b76e3984caa0**。

- pico_gap_standalone-v0.2.uf2：持久应用，不是旧版 RAM 采集固件。
- pico_gap_standalone-v0.2.elf：对应的 ELF 和符号文件。
- BUILD.json：具体算法开关以及十份对应源码的 SHA256。
- resource-audit.json：链接器分区、缓冲大小与静态栈分析，不代表运行时堆栈高水位。

构建使用 Pico SDK2.3.1、Arm GNU14.2.Rel1／GCC14.2.1，SDK 板型 pico。INTEGER_FFT／INTEGER_FAST 开启；WHITEN_FLOAT／MAG_CACHE／PICO_NO_FLASH 关闭。见[构建说明](../README_ZH.md)，不能省略开关并假设默认 CMake 就会生成此镜像。

替换别人的应用前先备份 Flash。按住 BOOTSEL 接入 USB，把 UF2 复制到 RPI-RP2，或用 picotool2.3.1 的 load -v 后 reboot。此操作会替换应用。正常上电无需电脑重载，串口号可能重新分配。

已完成写入校验、Flash 背景通信、软重启和无 Pico 电脑串口读取测试。此前正向手机测试是同源码／选项的 RAM 镜像。已知角度手机复测和物理断电测试仍待进行。本固件尚未达到新鲜目标和 0.2–0.5 秒验收要求，不含电机命令。

公开 ELF 已去除包含本机路径的调试信息；可装载二进制内容与原文件逐字一致。原始调试 ELF 只留本地，UF2 未变。
