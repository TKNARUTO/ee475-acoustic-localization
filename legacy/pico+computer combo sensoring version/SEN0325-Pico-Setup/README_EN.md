# Retained capture and desktop receiver

The Windows Python app computes bearing; Pico only supplies synchronous USB capture in this baseline. Use the start/update wrappers in the template root. Do not run this receiver while the new standalone viewer owns the same serial port.

The supplied firmware is v0.6-RX2 RAM-only and must be reloaded after power loss. Adjacent main.c/CMakeLists.txt/link_frame.h are v0.8-BRIDGE development source, not established matching v0.6 build source. Optional bridge_config.json remains disabled. See [firmware provenance](firmware/README_EN.md) and [full template instructions](../README_EN.md).

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](../PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
