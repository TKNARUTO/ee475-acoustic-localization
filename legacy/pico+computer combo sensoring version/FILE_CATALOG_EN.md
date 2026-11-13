# Complete file catalog

Paths are relative to the template root; runtime logs are excluded.

| File | Role |
|---|---|
| [.gitignore](<.gitignore>) | Keep newly generated logs/imports/environments/credentials out of future sharing. |
| [AGENTS.md](<AGENTS.md>) | Teammate/agent scope and rules for preserving this baseline. |
| [AGENTS_EN.md](<AGENTS_EN.md>) | English documentation or language-navigation entry. |
| [AGENTS_ZH.md](<AGENTS_ZH.md>) | Chinese documentation. |
| [FILE_CATALOG.md](<FILE_CATALOG.md>) | Complete relative file-to-role index for this template. |
| [FILE_CATALOG_EN.md](<FILE_CATALOG_EN.md>) | English documentation or language-navigation entry. |
| [FILE_CATALOG_ZH.md](<FILE_CATALOG_ZH.md>) | Chinese documentation. |
| [PLATFORM_EN.md](<PLATFORM_EN.md>) | English documentation or language-navigation entry. |
| [PLATFORM_ZH.md](<PLATFORM_ZH.md>) | Chinese documentation. |
| [README.md](<README.md>) | Stable combo architecture, usage and explicit v0.6-binary / v0.8-source provenance. |
| [README_EN.md](<README_EN.md>) | English documentation or language-navigation entry. |
| [README_ZH.md](<README_ZH.md>) | Chinese documentation. |
| [SEN0325-Pico-Setup/Build.ps1](<SEN0325-Pico-Setup/Build.ps1>) | Owner-specific firmware build helper; not a v0.6 source reproduction. |
| [SEN0325-Pico-Setup/CMakeLists.txt](<SEN0325-Pico-Setup/CMakeLists.txt>) | v0.8-BRIDGE development build definition; not the shipped v0.6 binary's asserted source. |
| [SEN0325-Pico-Setup/Load-RAM.ps1](<SEN0325-Pico-Setup/Load-RAM.ps1>) | Owner-specific RAM loading helper; normal template uses the desktop launcher. |
| [SEN0325-Pico-Setup/Monitor.ps1](<SEN0325-Pico-Setup/Monitor.ps1>) | Owner-specific serial diagnostic helper, not automatically run. |
| [SEN0325-Pico-Setup/README.md](<SEN0325-Pico-Setup/README.md>) | Receiver folder use and firmware provenance. |
| [SEN0325-Pico-Setup/README_EN.md](<SEN0325-Pico-Setup/README_EN.md>) | English documentation or language-navigation entry. |
| [SEN0325-Pico-Setup/README_ZH.md](<SEN0325-Pico-Setup/README_ZH.md>) | Chinese documentation. |
| [SEN0325-Pico-Setup/app_controls.py](<SEN0325-Pico-Setup/app_controls.py>) | Receive-only scan/profile controls. |
| [SEN0325-Pico-Setup/app_instance.py](<SEN0325-Pico-Setup/app_instance.py>) | Local single-instance and graceful focus/restart coordination. |
| [SEN0325-Pico-Setup/array_geometry.json](<SEN0325-Pico-Setup/array_geometry.json>) | Microphone positions and display reference settings; check physical calibration. |
| [SEN0325-Pico-Setup/arrival_dsp.py](<SEN0325-Pico-Setup/arrival_dsp.py>) | Matched-envelope arrival-consensus helper. |
| [SEN0325-Pico-Setup/beacon-audio/coded-gap-v1-right-only.wav](<SEN0325-Pico-Setup/beacon-audio/coded-gap-v1-right-only.wav>) | Bundled HF2 gap reference WAV used by the desktop receiver. |
| [SEN0325-Pico-Setup/beacon_dsp.py](<SEN0325-Pico-Setup/beacon_dsp.py>) | Built-in beacon templates, code detection and estimator routing. |
| [SEN0325-Pico-Setup/beacon_importer.py](<SEN0325-Pico-Setup/beacon_importer.py>) | Validate and import compatible local reference audio. |
| [SEN0325-Pico-Setup/bridge_config.json](<SEN0325-Pico-Setup/bridge_config.json>) | Optional UART bridge configuration; enabled remains false. |
| [SEN0325-Pico-Setup/check_protocol.py](<SEN0325-Pico-Setup/check_protocol.py>) | Earlier diagnostic serial protocol checker; hardware access only in a separate bench task. |
| [SEN0325-Pico-Setup/crc32_fast.h](<SEN0325-Pico-Setup/crc32_fast.h>) | C CRC32 lookup implementation. |
| [SEN0325-Pico-Setup/direction_diagnostics.py](<SEN0325-Pico-Setup/direction_diagnostics.py>) | Local finite recording/event diagnostic support. |
| [SEN0325-Pico-Setup/direction_estimator.py](<SEN0325-Pico-Setup/direction_estimator.py>) | Phase/geometry bearing support and calibration helpers. |
| [SEN0325-Pico-Setup/esp32_bridge.py](<SEN0325-Pico-Setup/esp32_bridge.py>) | Optional PC-to-Pico UART relay; disabled in this baseline. |
| [SEN0325-Pico-Setup/firmware/README.md](<SEN0325-Pico-Setup/firmware/README.md>) | English documentation or language-navigation entry. |
| [SEN0325-Pico-Setup/firmware/README.txt](<SEN0325-Pico-Setup/firmware/README.txt>) | Binary version, hash and source-mismatch explanation. |
| [SEN0325-Pico-Setup/firmware/README_EN.md](<SEN0325-Pico-Setup/firmware/README_EN.md>) | English documentation or language-navigation entry. |
| [SEN0325-Pico-Setup/firmware/README_ZH.md](<SEN0325-Pico-Setup/firmware/README_ZH.md>) | Chinese documentation. |
| [SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.elf](<SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.elf>) | Validated v0.6-RX2 RAM executable/debug pair. |
| [SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.uf2](<SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.uf2>) | Validated v0.6-RX2 RAM executable/debug pair. |
| [SEN0325-Pico-Setup/highband_dsp.py](<SEN0325-Pico-Setup/highband_dsp.py>) | High-frequency matched-filter/delay estimation. |
| [SEN0325-Pico-Setup/joint_delay_dsp.py](<SEN0325-Pico-Setup/joint_delay_dsp.py>) | Joint delay-search support. |
| [SEN0325-Pico-Setup/link_frame.h](<SEN0325-Pico-Setup/link_frame.h>) | v0.8 bridge CRC16/frame validation source reference. |
| [SEN0325-Pico-Setup/main.c](<SEN0325-Pico-Setup/main.c>) | v0.8-BRIDGE development C source retained separately from the validated v0.6 executable. |
| [SEN0325-Pico-Setup/make_regular_tones.py](<SEN0325-Pico-Setup/make_regular_tones.py>) | Earlier tone-generation utility; not part of the receive-only UI. |
| [SEN0325-Pico-Setup/radar_canvas.py](<SEN0325-Pico-Setup/radar_canvas.py>) | 2D direction/radar canvas. |
| [SEN0325-Pico-Setup/raw_packet.py](<SEN0325-Pico-Setup/raw_packet.py>) | Binary PCM framing, CRC32 and transport health parsing. |
| [SEN0325-Pico-Setup/refresh_and_start.py](<SEN0325-Pico-Setup/refresh_and_start.py>) | Compile-check sources and start/focus/gracefully restart only this app copy. |
| [SEN0325-Pico-Setup/release_info.py](<SEN0325-Pico-Setup/release_info.py>) | Desktop release identity and source fingerprint. |
| [SEN0325-Pico-Setup/requirements.txt](<SEN0325-Pico-Setup/requirements.txt>) | Pinned Python runtime package list. |
| [SEN0325-Pico-Setup/runtime_tuning.py](<SEN0325-Pico-Setup/runtime_tuning.py>) | Inter-capture scheduling settings. |
| [SEN0325-Pico-Setup/sen0325_i2s.pio](<SEN0325-Pico-Setup/sen0325_i2s.pio>) | Synchronous parallel I2S capture program source. |
| [SEN0325-Pico-Setup/sen0325_launcher.py](<SEN0325-Pico-Setup/sen0325_launcher.py>) | USB session, RAM image loading, packet capture and desktop DSP dispatch. |
| [SEN0325-Pico-Setup/sen0325_simple_view.py](<SEN0325-Pico-Setup/sen0325_simple_view.py>) | Main English desktop receiver interface. |
| [SEN0325-Pico-Setup/sen0325_view.py](<SEN0325-Pico-Setup/sen0325_view.py>) | Earlier diagnostic view retained with the app sources. |
| [SEN0325-Pico-Setup/signal_scope.py](<SEN0325-Pico-Setup/signal_scope.py>) | Received signal waveform/spectrum visualization. |
| [SEN0325-Pico-Setup/tone_filter.h](<SEN0325-Pico-Setup/tone_filter.h>) | Earlier narrowband diagnostic filter source. |
| [SEN0325-Pico-Setup/tracking_audio.py](<SEN0325-Pico-Setup/tracking_audio.py>) | Audio/reference utility support; no active PC playback control. |
| [SEN0325-Pico-Setup/verify_ram.py](<SEN0325-Pico-Setup/verify_ram.py>) | Reject UF2 payloads that do not target RP2040 SRAM only. |
| [SHA256SUMS.txt](<SHA256SUMS.txt>) | All-file SHA-256 checksums except itself. |
| [SOURCE_MANIFEST.json](<SOURCE_MANIFEST.json>) | Original and revised file provenance. |
| [Setup-Windows.ps1](<Setup-Windows.ps1>) | Create a project-local Python/Tk environment and install pinned dependencies. |
| [TEMPLATE_VALIDATION.json](<TEMPLATE_VALIDATION.json>) | Offline archive checks and what they do not establish. |
| [Update.cmd](<Update.cmd>) | Original wrapper: check local source and gracefully restart the desktop receiver. |
| [VALIDATION.md](<VALIDATION.md>) | English documentation or language-navigation entry. |
| [VALIDATION_EN.md](<VALIDATION_EN.md>) | English documentation or language-navigation entry. |
| [VALIDATION_ZH.md](<VALIDATION_ZH.md>) | Chinese documentation. |
| [android-player/CHANGELOG.md](<android-player/CHANGELOG.md>) | Phone transmitter installation/use/history documentation. |
| [android-player/CHANGELOG_EN.md](<android-player/CHANGELOG_EN.md>) | English documentation or language-navigation entry. |
| [android-player/CHANGELOG_ZH.md](<android-player/CHANGELOG_ZH.md>) | Chinese documentation. |
| [android-player/QUICKSTART_EN.md](<android-player/QUICKSTART_EN.md>) | English documentation or language-navigation entry. |
| [android-player/QUICKSTART_ZH.md](<android-player/QUICKSTART_ZH.md>) | Phone transmitter installation/use/history documentation. |
| [android-player/README.md](<android-player/README.md>) | Phone transmitter installation/use/history documentation. |
| [android-player/README_EN.md](<android-player/README_EN.md>) | English documentation or language-navigation entry. |
| [android-player/README_ZH.md](<android-player/README_ZH.md>) | Chinese documentation. |
| [android-player/releases/BeaconLoop-1.2.apk](<android-player/releases/BeaconLoop-1.2.apk>) | Installable Beacon Loop1.2 phone transmitter; no key/toolchain files bundled. |
| [audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3](<audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3>) | Matching phone HF2 gap audio or corrected default-signal usage note. |
| [audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav](<audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav>) | Matching phone HF2 gap audio or corrected default-signal usage note. |
| [audio/phone/HF2-gap-test/README.md](<audio/phone/HF2-gap-test/README.md>) | English documentation or language-navigation entry. |
| [audio/phone/HF2-gap-test/README.txt](<audio/phone/HF2-gap-test/README.txt>) | Matching phone HF2 gap audio or corrected default-signal usage note. |
| [audio/phone/HF2-gap-test/README_EN.md](<audio/phone/HF2-gap-test/README_EN.md>) | English documentation or language-navigation entry. |
| [audio/phone/HF2-gap-test/README_ZH.md](<audio/phone/HF2-gap-test/README_ZH.md>) | Chinese documentation. |
| [docs/HARDWARE.md](<docs/HARDWARE.md>) | Template-specific hardware instructions. |
| [docs/HARDWARE_EN.md](<docs/HARDWARE_EN.md>) | English documentation or language-navigation entry. |
| [docs/HARDWARE_ZH.md](<docs/HARDWARE_ZH.md>) | Chinese documentation. |
| [docs/SETUP_WINDOWS.md](<docs/SETUP_WINDOWS.md>) | Template-specific setup windows instructions. |
| [docs/SETUP_WINDOWS_EN.md](<docs/SETUP_WINDOWS_EN.md>) | English documentation or language-navigation entry. |
| [docs/SETUP_WINDOWS_ZH.md](<docs/SETUP_WINDOWS_ZH.md>) | Chinese documentation. |
| [docs/USER_GUIDE.md](<docs/USER_GUIDE.md>) | Template-specific user guide instructions. |
| [docs/USER_GUIDE_EN.md](<docs/USER_GUIDE_EN.md>) | English documentation or language-navigation entry. |
| [docs/USER_GUIDE_ZH.md](<docs/USER_GUIDE_ZH.md>) | Chinese documentation. |
| [tests/README.md](<tests/README.md>) | Offline mock/synthetic check or instructions; no private recordings required. |
| [tests/README_EN.md](<tests/README_EN.md>) | English documentation or language-navigation entry. |
| [tests/README_ZH.md](<tests/README_ZH.md>) | Chinese documentation. |
| [tests/requirements-plots.txt](<tests/requirements-plots.txt>) | Optional plotting requirements. |
| [tests/verify_controls.py](<tests/verify_controls.py>) | Offline mock/synthetic check or instructions; no private recordings required. |
| [tests/verify_english_ui.py](<tests/verify_english_ui.py>) | Offline mock/synthetic check or instructions; no private recordings required. |
| [tests/verify_gap_beacon.py](<tests/verify_gap_beacon.py>) | Offline mock/synthetic check or instructions; no private recordings required. |
| [tests/verify_raw_packet.py](<tests/verify_raw_packet.py>) | Offline mock/synthetic check or instructions; no private recordings required. |
| [tools/launch.cmd](<tools/launch.cmd>) | Resolve Python and launch this copy's refresh_and_start.py. |
| [tools/verify_handoff.py](<tools/verify_handoff.py>) | Run six reproducible offline source/model/packet/firmware check groups. |
| [一键启动.cmd](<一键启动.cmd>) | Original wrapper: open/focus this template's desktop receiver. |

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
