# Beacon Loop 1.2 release record

## 12 November 2026 — documentation only

English and Chinese manuals are separated. Instructions now distinguish general phone-file import from the current independent Pico's fixed HF2 reference. Source, APK, audio, build scripts and local configuration are unchanged. Obsolete links to removed Android archives were removed.

## 5 November 2026 — retained 1.2 release

Version 1.2 / code 3 made HF2 gap the only bundled/default beacon. Local import, PCM looping and optional gain were retained; the old built-in selector was removed. Old built-in cache selections migrate to HF2 gap; custom cached files remain available; a missing cache falls back to the correctly labelled default. The intentional gap, waveform fades, frequency, sample rate and channel layout were preserved.

The recorded build used Windows, JDK 25.0.4.1+1, Android API 35 and Android 15 build-tools, with Java source/target 8. Runtime minimum is API 26 and target is API 35. Offline checks passed for APK build, v2/v3 signatures, ZIP alignment, package metadata, matching WAV and nine PcmGain tests. PC-reference waveform correlation was 0.9999999959766115. These are historical offline checks, not complete phone acceptance.

APK SHA-256: `c3a779101180ba396713b84a60b9d63abc326ab93a517d91444fc415ad440636`.
Signer certificate SHA-256: `32d13ff773b36c8438220db4fb63b6daf5e6da6d829b6ef11f7febe2571ce037`.
This signer matches original 1.0, not imported 1.1; direct update from that differently signed 1.1 is unsupported. See [usage/build instructions](README_EN.md) and unchanged [validation record](validation.json).
