# Matching HF2 gap phone audio

Use `01_LOCATE_18-22kHz_43ms-gap.wav` or its MP3. This is the default coded-gap signal in the retained combo. Sampling is 48 kHz, right channel only; each 4096-sample period has 2048 active + 2048 silent samples (42.67 ms + 42.67 ms). Do not trim the silence. Choose Gap test / 18–22 kHz and Start Scan in the receiver. Prefer WAV for reproducibility and record phone position/volume. Audibility and high-frequency output depend on the phone and listener; inaudibility and a fixed range are not guaranteed.

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](../../../PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
