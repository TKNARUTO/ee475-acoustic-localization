# Agent instructions for the retained combo

Read README_EN.md, FILE_CATALOG_EN.md and PLATFORM_EN.md before work. This template is phone -> SEN0325 -> Pico USB capture -> Windows bearing computation. It is not the independent Pico deployment.

- Preserve source/configuration/launchers/audio/APK/UF2/ELF; experiments belong in a separate copy.
- Keep v0.6-RX2 RAM binaries intact. Nearby v0.8-BRIDGE source is not a verified rebuild source for them; RAM requires reload after power loss.
- Keep bridge_config.json disabled for baseline comparisons. Motors and ESP32 firmware are outside this template.
- Do not suppress large turns solely because they are large. Separate held arrows, fresh observations, timing and physical accuracy.
- Phone performs playback; PC is receive-only. Preserve matching beacon, sample rate and channel mapping.
- Keep raw recordings, credentials, imported audio and toolchains local. Write validation output outside the frozen folder.
- Offline tests require no hardware. A hardware task needs explicit scope and exclusive device access.
- Update documentation/provenance for a new experiment; never silently overwrite this baseline.

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
