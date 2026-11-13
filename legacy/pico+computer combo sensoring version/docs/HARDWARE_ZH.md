# 旧组合接线

Pico 负责同步数字采集，Windows 负责方向计算。按 GPIO 名称和物理针脚接线，不凭未核实的左右视角。元件面朝上、USB 在上时 GP0–GP15 在左边；背面照片左右相反。

| SEN0325 标记 | Pico 信号 | 物理针脚 |
|---|---|---|
| VIN | 3V3 OUT | 36 |
| GND | GND | 13 |
| MIC_D0 | GP6 | 9 |
| MIC_D1 | GP7 | 10 |
| MIC_D2 | GP8 | 11 |
| MIC_D3 | GP9 | 12 |
| MIC_CK | GP10 | 14 |
| MIC_WS | GP11 | 15 |
| LED_CK | GP12 | 16 |
| LED_DA | GP13 | 17 |

保持已使用的 3.3 V 阵列测试供电，本归档未验证 5 V 板型。改线前断电；GPIO 为 3.3 V 逻辑，基线不使用灯环照明。

连接器丝印视角如下：
```text
LED_DA  LED_CK
MIC_D1  MIC_D0
MIC_D3  MIC_D2
MIC_CK  MIC_WS
GND     VIN
```

BCLK 为 3.072 MHz，WS 为 48 kHz，使用四路并行立体声 I2S。USB 通道顺序为 D0L、D0R、D1L、D1R、D2L、D2R、D3R_CENTER；D3L 不用。几何参考为半径 40 mm、外圈角度 0/60/120/180/240/300 度，声速 343 m/s。实际安装方向仍需已知角度测试；Set Front 是显示参考校准，不是测距。

旧组合不需要 ESP32，可选 UART 桥接关闭，未包含电机固件。不要让两个程序同时占用 Pico 串口。

平台与工具：电脑端使用 Windows 10/11、Python 3.12+（含 Tcl/Tk）；Pico 通过 USB 采集。手机播放器需 Android 8.0/API 26 或以上。运行旧固件不需要编译器；工具版本及限制见[平台说明](../PLATFORM_ZH.md)。当前独立 Pico 程序位于模板根目录上两级的 `pico-standalone/`，不包含在本 ZIP 内。
