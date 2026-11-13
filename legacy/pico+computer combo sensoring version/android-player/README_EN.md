# Included phone player: Beacon Loop 1.2

Install `releases/BeaconLoop-1.2.apk`. It requires Android API 26+ and targets API 35. Use the built-in HF2 gap beacon, or select a compatible local audio file. **Play loop** starts looping; **Pause** stops it. Set media volume on the phone. Keep **Normalize** off for baseline comparison and record position, distance and volume.

The 42.67 ms active / 42.67 ms silent pattern is intentional. Prefer WAV for repeatable comparisons; MP3 padding is not automatically removed. Optional Normalize changes overall gain by at most +3 dB with a peak limit; it does not change frequency, calibrate the array or guarantee longer range.

Version 1.2 uses the original 1.0 signing identity. It cannot directly replace the differently signed 1.1 installation; preserve needed application state before deciding how to replace it. The compact template includes the APK and documents only, not Android source, SDK/JDK or signing keys. No phone was installed or modified during this revision. See [release notes](CHANGELOG_EN.md).

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](../PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
