RETAINED DESKTOP COMBO FIRMWARE — v0.6-RX2

sen0325_setup-RAM.uf2 and sen0325_setup-RAM.elf are the retained executable pair.
UF2 SHA-256: 76470847618d44065001eba3615cf49e19e858a27839dd09543700e7d8471151
48 kHz, 4096 frames, seven signed-16-bit channels; existing GPIO and PCM order preserved.
USB: TX software FIFO 4096 B, RX FIFO / transfer buffer 512 B; USB full-speed packet size remains 64 B.
CRC32 is zlib-compatible. All UF2 payload targets SRAM, not Flash; power loss removes this RAM program.

The template launcher validates this UF2 before loading through an RPI-RP2 BOOTSEL drive or the optional configured picotool fallback.

IMPORTANT: parent-directory main.c/CMakeLists.txt identify v0.8-BRIDGE development source, not a verified source reproduction of this v0.6 image. Do not regenerate and overwrite this baseline merely by running Build.ps1. No matching v0.6 build source is asserted by this archive.


Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](../../PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
