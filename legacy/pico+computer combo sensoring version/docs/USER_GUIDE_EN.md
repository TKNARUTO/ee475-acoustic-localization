# Receiver use

1. Open the template's 一键启动.cmd. It starts the computer-based receiver in coded-gap mode.
2. Start Scan after the intended Pico is connected. If needed, use BOOTSEL to load the supplied v0.6 RAM capture image.
3. Loop the included HF2 gap WAV/MP3 or Beacon Loop1.2 built-in beacon on the phone. Begin with a documented fixed position near0.5m and moderate media volume.
4. Read the direction plot together with code/validity, signal waveform and spectrum. A held arrow may persist1.5s and does not prove a new measurement. Plot rings do not measure range.
5. Use Set Front to choose a visual reference. Real large turns remain allowed. A controlled known-angle test is still needed to assess accuracy.
6. Use Import Beacon only for a compatible periodic localization code; phone playback and receiver reference must match. User imports are local and were excluded from this archive.
7. Stop Scan or close the receiver before another tool takes the Pico COM port. Update.cmd requests a graceful local restart and waits for recording closure.

The PC emits no beacon playback. Deliberate phone pauses and unrecorded motion are not transport bugs. No motor or distance-sensor control is included.


Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](../PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
