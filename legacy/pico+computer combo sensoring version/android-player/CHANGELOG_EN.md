# Retained Android 1.2 release record

The 5 November 2026 release (version code 3) selected HF2 gap as the only built-in/default signal, retaining local import, PCM looping and optional bounded gain. The old built-in selector was removed. Old built-in cache names migrate to gap; custom choices remain cached; a missing cache falls back to the correctly labelled gap signal.

The source release recorded a successful APK build, signature/alignment/metadata checks, the gap-only asset inventory, source/APK/phone waveform agreement, reference correlation 0.999999996 and nine gain tests. These are historical build records, not new tests performed for this documentation revision. Phone installation, screen-off behavior, audio-focus behavior and physical localization were not established by packaging.

Certificate SHA-256: `32d13ff773b36c8438220db4fb63b6daf5e6da6d829b6ef11f7febe2571ce037`. It matches original 1.0, not the imported differently signed 1.1. No keys are distributed. Earlier APKs, old built-in audio and build outputs are outside this final compact template. Their old local paths are not runnable dependencies here. Frequency, sample rate, code, channels, intentional gap and boundary fades are unchanged.

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](../PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
