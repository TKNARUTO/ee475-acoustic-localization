# Stable combo hardware

The Pico supplies synchronous digital capture; the Windows app computes bearing. Use board GPIO labels rather than an unverified left/right view. With the Pico component side up and USB at the top, GP0..GP15 are on the left. A back-side photograph reverses the sides.

| SEN0325 label | Pico signal | Physical pin |
| --- | --- | --- |
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

Retain the already used 3.3 V microphone-test supply. This archive does not validate a 5 V revision. Disconnect power before rewiring; GPIO uses 3.3 V logic. LED ring illumination is not part of the baseline test.

The connector-label view is:
```text
LED_DA  LED_CK
MIC_D1  MIC_D0
MIC_D3  MIC_D2
MIC_CK  MIC_WS
GND     VIN
```

Capture uses 3.072 MHz BCLK, 48 kHz WS and four parallel stereo I2S lines. USB channel order is D0L,D0R,D1L,D1R,D2L,D2R,D3R_CENTER; D3L is unused. Geometry defaults to outer positions0,60,120,180,240,300degrees on a 40 mm radius with 343 m/s sound speed. Physical alignment still needs a known-angle check; Set Front is display calibration, not a measured distance.

An ESP32 is not needed for this computer+Pico template. Optional UART support is disabled and no motor firmware is included. Avoid running this receiver and another program against the same Pico COM port simultaneously.


Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](../PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
