# Documentation revision and package validation

On 12 November 2026, the six retained offline groups passed: Python syntax, launcher source, SRAM-only UF2 layout, receive-only controls, packet faults and gap model. No serial port, firmware flashing, phone installation or sound playback was used. No new physical accuracy/range acceptance is claimed.

This revision separates English and Chinese instructions, replaces stale local-history references with archive scope notes, refreshes file/provenance manifests and rebuilds the ZIP. Every non-document file is compared byte-for-byte with the backed-up original ZIP: source, scripts, configuration, requirements, UF2, ELF, APK and audio must remain unchanged. Every new ZIP entry is hash-checked against the final folder.

The original ZIP SHA-256 is `2fae8fad70b2501d3766234f89c724936717bccbcb042dd43b2300fd8b4a53d9`. Original source-relative paths/hashes remain in SOURCE_MANIFEST.json. Its own hash and the checksum file are excluded from manifest entries to avoid circular references; SHA256SUMS.txt covers the manifest. The final ZIP digest is recorded outside the ZIP.

The v0.6 binary / v0.8 source mismatch remains explicit and unresolved. RAM reloading, new-PC drivers, waveform compatibility, physical calibration, phone output and display hold behavior still require correct operation and separate bench verification.

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
