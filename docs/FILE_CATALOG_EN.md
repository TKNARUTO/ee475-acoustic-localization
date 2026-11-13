# Public project file catalog

Documentation baseline: 2026-11-12. 237 selected files. This is the local release selection, not a claim of a GitHub push or hardware acceptance.

Current roles: Pico computes bearing; ESP32 NodeMCU-32S receives/acknowledges; Android plays the beacon; the PC viewer is optional. Root Start.cmd and Update.cmd never flash firmware. Only the final Pico + PC comparison template and its exact ZIP remain under legacy.

Logs, raw recordings, keys, device backups, machine settings and build/cache outputs are excluded. Public test source and designated firmware releases remain selected. Supplied reference PDF/DOCX/PPTX retain their original language. SHA256SUMS.txt covers every selected file except itself.

[中文](FILE_CATALOG_ZH.md) · [Machine-readable CSV](FILE_CATALOG.csv)

| File | Role | Function |
|---|---|---|
| `.gitattributes` | Project setup, documentation and integrity | Git text/binary and line-ending rules |
| `.gitignore` | Project setup, documentation and integrity | Keep local logs, builds, recordings and keys out of Git |
| `AGENTS.md` | Project setup, documentation and integrity | Entry for repository constraints and agent handoff |
| `README.md` | Project setup, documentation and integrity | Setup, file roles and validation limits |
| `README_EN.md` | Project setup, documentation and integrity | Setup, file roles and validation limits (English) |
| `README_ZH.md` | Project setup, documentation and integrity | Setup, file roles and validation limits (Chinese) |
| `SHA256SUMS.txt` | Project setup, documentation and integrity | SHA256 of all selected files except this checksum file itself |
| `Setup-Windows.ps1` | Project setup, documentation and integrity | Prepare the optional Windows viewer dependencies |
| `Start.cmd` | Project setup, documentation and integrity | Open/focus the current standalone monitor; never flash firmware |
| `Update.cmd` | Project setup, documentation and integrity | Validate and restart local viewer; no Git download or firmware write |
| `android-player/Build.cmd` | Android local looping transmitter | Windows entry for the Android build script |
| `android-player/Build.ps1` | Android local looping transmitter | Build the Android application with configured local SDK tools |
| `android-player/CHANGELOG.md` | Android local looping transmitter | Version changes with their scope and status |
| `android-player/CHANGELOG_EN.md` | Android local looping transmitter | Version changes with their scope and status (English) |
| `android-player/CHANGELOG_ZH.md` | Android local looping transmitter | Version changes with their scope and status (Chinese) |
| `android-player/README.md` | Android local looping transmitter | Setup, file roles and validation limits |
| `android-player/README_EN.md` | Android local looping transmitter | Setup, file roles and validation limits (English) |
| `android-player/README_ZH.md` | Android local looping transmitter | Setup, file roles and validation limits (Chinese) |
| `android-player/app/src/main/AndroidManifest.xml` | Android local looping transmitter | Android app identity, permissions and service declarations |
| `android-player/app/src/main/assets/gap-beacon.wav` | Android local looping transmitter | Transmitter/reference waveform; keep it matched to the receiver template |
| `android-player/app/src/main/java/org/ee475/beaconloop/AudioLoader.java` | Android local looping transmitter | Decode selected audio into playback PCM |
| `android-player/app/src/main/java/org/ee475/beaconloop/LoopService.java` | Android local looping transmitter | Local foreground audio looping service |
| `android-player/app/src/main/java/org/ee475/beaconloop/MainActivity.java` | Android local looping transmitter | Android audio selection and simple playback controls |
| `android-player/app/src/main/java/org/ee475/beaconloop/PcmGain.java` | Android local looping transmitter | Bounded optional PCM gain without silently changing frequency |
| `android-player/app/src/main/res/drawable/ic_beacon.xml` | Android local looping transmitter | Component implementation or reproducible support utility: ic_beacon.xml |
| `android-player/app/src/main/res/values/styles.xml` | Android local looping transmitter | Component implementation or reproducible support utility: styles.xml |
| `android-player/releases/BeaconLoop-1.2.apk` | Android local looping transmitter | Installable Android local beacon-loop player |
| `android-player/sdk-downloads.json` | Android local looping transmitter | Declared SDK dependency sources for reproducible setup |
| `android-player/tests/PcmGainTest.java` | Android local looping transmitter | Unit checks of PCM gain, bounds and clipping behavior |
| `android-player/toolchain.example.json` | Android local looping transmitter | Portable example of local toolchain settings; no real credentials |
| `android-player/tools/merge_apk.py` | Android local looping transmitter | Assemble Android APK components during the local build |
| `android-player/validation.json` | Android local looping transmitter | Recorded component verification results and boundaries |
| `audio/README.md` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits |
| `audio/README_EN.md` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits (English) |
| `audio/README_ZH.md` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits (Chinese) |
| `audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3` | Fixed HF2 transmitter/reference | Transmitter/reference waveform; keep it matched to the receiver template |
| `audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav` | Fixed HF2 transmitter/reference | Transmitter/reference waveform; keep it matched to the receiver template |
| `audio/phone/HF2-gap-test/README.md` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits |
| `audio/phone/HF2-gap-test/README.txt` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits |
| `audio/phone/HF2-gap-test/README_EN.md` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits (English) |
| `audio/phone/HF2-gap-test/README_ZH.md` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits (Chinese) |
| `audio/phone/README.md` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits |
| `audio/phone/README.txt` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits |
| `audio/phone/README_EN.md` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits (English) |
| `audio/phone/README_ZH.md` | Fixed HF2 transmitter/reference | Setup, file roles and validation limits (Chinese) |
| `docs/FILE_CATALOG.csv` | Project setup, documentation and integrity | Complete selected-file role and function index |
| `docs/FILE_CATALOG.md` | Project setup, documentation and integrity | Complete selected-file role and function index |
| `docs/FILE_CATALOG_EN.md` | Project setup, documentation and integrity | Complete selected-file role and function index (English) |
| `docs/FILE_CATALOG_ZH.md` | Project setup, documentation and integrity | Complete selected-file role and function index (Chinese) |
| `docs/HARDWARE_EN.md` | Project setup, documentation and integrity | Verified board identification, GPIO wiring and power roles (English) |
| `docs/HARDWARE_ZH.md` | Project setup, documentation and integrity | Verified board identification, GPIO wiring and power roles (Chinese) |
| `docs/INTEGRATION_EN.md` | Project setup, documentation and integrity | System integration architecture, constraints and predicted faults (English) |
| `docs/INTEGRATION_ZH.md` | Project setup, documentation and integrity | System integration architecture, constraints and predicted faults (Chinese) |
| `docs/RELEASE_NOTEBOOK_EN.md` | Project setup, documentation and integrity | Component implementation or reproducible support utility: RELEASE_NOTEBOOK_EN.md |
| `docs/RELEASE_NOTEBOOK_ZH.md` | Project setup, documentation and integrity | Component implementation or reproducible support utility: RELEASE_NOTEBOOK_ZH.md |
| `docs/SETUP_WINDOWS_EN.md` | Project setup, documentation and integrity | Windows runtime setup and current monitor launch procedure (English) |
| `docs/SETUP_WINDOWS_ZH.md` | Project setup, documentation and integrity | Windows runtime setup and current monitor launch procedure (Chinese) |
| `docs/SHARING_EN.md` | Project setup, documentation and integrity | Public release selection, privacy and synchronization checks (English) |
| `docs/SHARING_ZH.md` | Project setup, documentation and integrity | Public release selection, privacy and synchronization checks (Chinese) |
| `docs/TEAM_HANDOFF_EN.md` | Project setup, documentation and integrity | Teammate/agent ownership, interfaces and next-stage priorities (English) |
| `docs/TEAM_HANDOFF_ZH.md` | Project setup, documentation and integrity | Teammate/agent ownership, interfaces and next-stage priorities (Chinese) |
| `docs/VALIDATION_EN.md` | Project setup, documentation and integrity | Reproduction commands, test outcomes and unresolved checks (English) |
| `docs/VALIDATION_ZH.md` | Project setup, documentation and integrity | Reproduction commands, test outcomes and unresolved checks (Chinese) |
| `esp32-link/README.md` | NodeMCU-32S receive/ACK component | Setup, file roles and validation limits |
| `esp32-link/README_EN.md` | NodeMCU-32S receive/ACK component | Setup, file roles and validation limits (English) |
| `esp32-link/README_ZH.md` | NodeMCU-32S receive/ACK component | Setup, file roles and validation limits (Chinese) |
| `esp32-link/gap_receiver/README.md` | NodeMCU-32S receive/ACK component | Setup, file roles and validation limits |
| `esp32-link/gap_receiver/README_EN.md` | NodeMCU-32S receive/ACK component | Setup, file roles and validation limits (English) |
| `esp32-link/gap_receiver/README_ZH.md` | NodeMCU-32S receive/ACK component | Setup, file roles and validation limits (Chinese) |
| `esp32-link/gap_receiver/firmware/BUILD.json` | NodeMCU-32S receive/ACK component | Frozen source/artifact identity and build/deployment metadata |
| `esp32-link/gap_receiver/firmware/README_EN.md` | NodeMCU-32S receive/ACK component | Setup, file roles and validation limits (English) |
| `esp32-link/gap_receiver/firmware/README_ZH.md` | NodeMCU-32S receive/ACK component | Setup, file roles and validation limits (Chinese) |
| `esp32-link/gap_receiver/gap_diagnostics.h` | NodeMCU-32S receive/ACK component | Print received raw fields independently of control-target state |
| `esp32-link/gap_receiver/gap_protocol.h` | NodeMCU-32S receive/ACK component | CRC/session/sequence parsing and target expiry state machine |
| `esp32-link/gap_receiver/gap_receiver.ino` | NodeMCU-32S receive/ACK component | NodeMCU-32S UART2 receive/ACK application; no motor commands |
| `esp32-link/gap_receiver/gap_self_tests.h` | NodeMCU-32S receive/ACK component | Receiver startup tests on temporary state before enabling UART |
| `esp32-link/gap_receiver/tests/host_protocol_test.cpp` | NodeMCU-32S receive/ACK component | Run real ESP protocol/diagnostic tests with a host compiler |
| `legacy/pico+computer combo sensoring version.zip` | Final combo archive | Exact byte-matching archive of the final Pico + PC template |
| `legacy/pico+computer combo sensoring version/.gitignore` | Retained final Pico + PC template | Frozen comparison: Keep local logs, builds, recordings and keys out of Git |
| `legacy/pico+computer combo sensoring version/AGENTS.md` | Retained final Pico + PC template | Frozen comparison: Entry for repository constraints and agent handoff |
| `legacy/pico+computer combo sensoring version/AGENTS_EN.md` | Retained final Pico + PC template | Frozen comparison: Repository constraints and coding-agent handoff (English) |
| `legacy/pico+computer combo sensoring version/AGENTS_ZH.md` | Retained final Pico + PC template | Frozen comparison: Repository constraints and coding-agent handoff (Chinese) |
| `legacy/pico+computer combo sensoring version/FILE_CATALOG.md` | Retained final Pico + PC template | Frozen comparison: Complete selected-file role and function index |
| `legacy/pico+computer combo sensoring version/FILE_CATALOG_EN.md` | Retained final Pico + PC template | Frozen comparison: Complete selected-file role and function index (English) |
| `legacy/pico+computer combo sensoring version/FILE_CATALOG_ZH.md` | Retained final Pico + PC template | Frozen comparison: Complete selected-file role and function index (Chinese) |
| `legacy/pico+computer combo sensoring version/PLATFORM_EN.md` | Retained final Pico + PC template | Frozen comparison: Specific hardware and build-tool versions for this component (English) |
| `legacy/pico+computer combo sensoring version/PLATFORM_ZH.md` | Retained final Pico + PC template | Frozen comparison: Specific hardware and build-tool versions for this component (Chinese) |
| `legacy/pico+computer combo sensoring version/README.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits |
| `legacy/pico+computer combo sensoring version/README_EN.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (English) |
| `legacy/pico+computer combo sensoring version/README_ZH.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (Chinese) |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/Build.ps1` | Retained final Pico + PC template | Frozen comparison: Build the Android application with configured local SDK tools |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/CMakeLists.txt` | Retained final Pico + PC template | Frozen comparison: Pico SDK source selection, target options and build rules |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/Load-RAM.ps1` | Retained final Pico + PC template | Frozen comparison: Load only the retained combo's temporary capture RAM image |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/Monitor.ps1` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: Monitor.ps1 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/README.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/README_EN.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (English) |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/README_ZH.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (Chinese) |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/app_controls.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: app_controls.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/app_instance.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: app_instance.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/array_geometry.json` | Retained final Pico + PC template | Frozen comparison: Microphone channel positions and array angle convention |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/arrival_dsp.py` | Retained final Pico + PC template | Frozen comparison: PC arrival-peak consensus and geometric fitting reference |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/beacon-audio/coded-gap-v1-right-only.wav` | Retained final Pico + PC template | Frozen comparison: Transmitter/reference waveform; keep it matched to the receiver template |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/beacon_dsp.py` | Retained final Pico + PC template | Frozen comparison: PC reference beacon generation, profiles and detection |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/beacon_importer.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: beacon_importer.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/bridge_config.json` | Retained final Pico + PC template | Frozen comparison: Shared configuration, provenance or structured verification: bridge_config.json |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/check_protocol.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: check_protocol.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/crc32_fast.h` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: crc32_fast.h |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/direction_diagnostics.py` | Retained final Pico + PC template | Frozen comparison: Local capture of direction-failure diagnostics; data not shipped |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/direction_estimator.py` | Retained final Pico + PC template | Frozen comparison: PC direction estimation and result coordination |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/esp32_bridge.py` | Retained final Pico + PC template | Frozen comparison: Retained PC-result bridge helper, not standalone Pico estimation |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/README.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/README.txt` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/README_EN.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (English) |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/README_ZH.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (Chinese) |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.elf` | Retained final Pico + PC template | Frozen comparison: Firmware executable/symbol artifact for debugging and resource analysis |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.uf2` | Retained final Pico + PC template | Frozen comparison: Compiled firmware image; consult build identity before deployment |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/highband_dsp.py` | Retained final Pico + PC template | Frozen comparison: PC high-band matching and localization reference |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/joint_delay_dsp.py` | Retained final Pico + PC template | Frozen comparison: PC joint-delay/direction search reference |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/link_frame.h` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: link_frame.h |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/main.c` | Retained final Pico + PC template | Frozen comparison: Retained Pico capture firmware used with PC-side localization |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/make_regular_tones.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: make_regular_tones.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/radar_canvas.py` | Retained final Pico + PC template | Frozen comparison: Draw the retained PC estimator radar display |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/raw_packet.py` | Retained final Pico + PC template | Frozen comparison: Parse the preserved Pico-to-PC raw audio packet format |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/refresh_and_start.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: refresh_and_start.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/release_info.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: release_info.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/requirements.txt` | Retained final Pico + PC template | Frozen comparison: Declared Python dependencies for this component |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/runtime_tuning.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: runtime_tuning.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/sen0325_i2s.pio` | Retained final Pico + PC template | Frozen comparison: PIO program for synchronous microphone I2S sampling |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/sen0325_launcher.py` | Retained final Pico + PC template | Frozen comparison: Retained PC estimator launcher; may load its capture RAM image |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/sen0325_simple_view.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: sen0325_simple_view.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/sen0325_view.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: sen0325_view.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/signal_scope.py` | Retained final Pico + PC template | Frozen comparison: Show signal/spectrum diagnostics in the retained PC application |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/tone_filter.h` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: tone_filter.h |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/tracking_audio.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: tracking_audio.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/verify_ram.py` | Retained final Pico + PC template | Frozen comparison: Check the retained combo capture RAM image identity |
| `legacy/pico+computer combo sensoring version/SHA256SUMS.txt` | Retained final Pico + PC template | Frozen comparison: SHA256 of all selected files except this checksum file itself |
| `legacy/pico+computer combo sensoring version/SOURCE_MANIFEST.json` | Retained final Pico + PC template | Frozen comparison: Frozen template source identities and provenance |
| `legacy/pico+computer combo sensoring version/Setup-Windows.ps1` | Retained final Pico + PC template | Frozen comparison: Prepare the optional Windows viewer dependencies |
| `legacy/pico+computer combo sensoring version/TEMPLATE_VALIDATION.json` | Retained final Pico + PC template | Frozen comparison: Frozen-template validation evidence and limits |
| `legacy/pico+computer combo sensoring version/Update.cmd` | Retained final Pico + PC template | Frozen comparison: Retained PC-computation launcher/update; may load combo capture RAM firmware |
| `legacy/pico+computer combo sensoring version/VALIDATION.md` | Retained final Pico + PC template | Frozen comparison: Reproduction commands, test outcomes and unresolved checks |
| `legacy/pico+computer combo sensoring version/VALIDATION_EN.md` | Retained final Pico + PC template | Frozen comparison: Reproduction commands, test outcomes and unresolved checks (English) |
| `legacy/pico+computer combo sensoring version/VALIDATION_ZH.md` | Retained final Pico + PC template | Frozen comparison: Reproduction commands, test outcomes and unresolved checks (Chinese) |
| `legacy/pico+computer combo sensoring version/android-player/CHANGELOG.md` | Retained final Pico + PC template | Frozen comparison: Version changes with their scope and status |
| `legacy/pico+computer combo sensoring version/android-player/CHANGELOG_EN.md` | Retained final Pico + PC template | Frozen comparison: Version changes with their scope and status (English) |
| `legacy/pico+computer combo sensoring version/android-player/CHANGELOG_ZH.md` | Retained final Pico + PC template | Frozen comparison: Version changes with their scope and status (Chinese) |
| `legacy/pico+computer combo sensoring version/android-player/QUICKSTART_EN.md` | Retained final Pico + PC template | Frozen comparison: Short component installation and first-use instructions (English) |
| `legacy/pico+computer combo sensoring version/android-player/QUICKSTART_ZH.md` | Retained final Pico + PC template | Frozen comparison: Short component installation and first-use instructions (Chinese) |
| `legacy/pico+computer combo sensoring version/android-player/README.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits |
| `legacy/pico+computer combo sensoring version/android-player/README_EN.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (English) |
| `legacy/pico+computer combo sensoring version/android-player/README_ZH.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (Chinese) |
| `legacy/pico+computer combo sensoring version/android-player/releases/BeaconLoop-1.2.apk` | Retained final Pico + PC template | Frozen comparison: Installable Android local beacon-loop player |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3` | Retained final Pico + PC template | Frozen comparison: Transmitter/reference waveform; keep it matched to the receiver template |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav` | Retained final Pico + PC template | Frozen comparison: Transmitter/reference waveform; keep it matched to the receiver template |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/README.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/README.txt` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/README_EN.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (English) |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/README_ZH.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (Chinese) |
| `legacy/pico+computer combo sensoring version/docs/HARDWARE.md` | Retained final Pico + PC template | Frozen comparison: Verified board identification, GPIO wiring and power roles |
| `legacy/pico+computer combo sensoring version/docs/HARDWARE_EN.md` | Retained final Pico + PC template | Frozen comparison: Verified board identification, GPIO wiring and power roles (English) |
| `legacy/pico+computer combo sensoring version/docs/HARDWARE_ZH.md` | Retained final Pico + PC template | Frozen comparison: Verified board identification, GPIO wiring and power roles (Chinese) |
| `legacy/pico+computer combo sensoring version/docs/SETUP_WINDOWS.md` | Retained final Pico + PC template | Frozen comparison: Windows runtime setup and current monitor launch procedure |
| `legacy/pico+computer combo sensoring version/docs/SETUP_WINDOWS_EN.md` | Retained final Pico + PC template | Frozen comparison: Windows runtime setup and current monitor launch procedure (English) |
| `legacy/pico+computer combo sensoring version/docs/SETUP_WINDOWS_ZH.md` | Retained final Pico + PC template | Frozen comparison: Windows runtime setup and current monitor launch procedure (Chinese) |
| `legacy/pico+computer combo sensoring version/docs/USER_GUIDE.md` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: USER_GUIDE.md |
| `legacy/pico+computer combo sensoring version/docs/USER_GUIDE_EN.md` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: USER_GUIDE_EN.md |
| `legacy/pico+computer combo sensoring version/docs/USER_GUIDE_ZH.md` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: USER_GUIDE_ZH.md |
| `legacy/pico+computer combo sensoring version/tests/README.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits |
| `legacy/pico+computer combo sensoring version/tests/README_EN.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (English) |
| `legacy/pico+computer combo sensoring version/tests/README_ZH.md` | Retained final Pico + PC template | Frozen comparison: Setup, file roles and validation limits (Chinese) |
| `legacy/pico+computer combo sensoring version/tests/requirements-plots.txt` | Retained final Pico + PC template | Frozen comparison: Component documentation, dependency or project reference: requirements-plots.txt |
| `legacy/pico+computer combo sensoring version/tests/verify_controls.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: verify_controls.py |
| `legacy/pico+computer combo sensoring version/tests/verify_english_ui.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: verify_english_ui.py |
| `legacy/pico+computer combo sensoring version/tests/verify_gap_beacon.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: verify_gap_beacon.py |
| `legacy/pico+computer combo sensoring version/tests/verify_raw_packet.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: verify_raw_packet.py |
| `legacy/pico+computer combo sensoring version/tools/launch.cmd` | Retained final Pico + PC template | Frozen comparison: Retained PC-computation launcher/update; may load combo capture RAM firmware |
| `legacy/pico+computer combo sensoring version/tools/verify_handoff.py` | Retained final Pico + PC template | Frozen comparison: Component implementation or reproducible support utility: verify_handoff.py |
| `legacy/pico+computer combo sensoring version/一键启动.cmd` | Retained final Pico + PC template | Frozen comparison: Retained PC-computation launcher/update; may load combo capture RAM firmware |
| `pico-standalone/CMakeLists.txt` | Current independent Pico component | Pico SDK source selection, target options and build rules |
| `pico-standalone/COMMUNICATION_NOTEBOOK_EN.md` | Current independent Pico component | Communication decisions, trials and remaining acceptance checks (English) |
| `pico-standalone/COMMUNICATION_NOTEBOOK_ZH.md` | Current independent Pico component | Communication decisions, trials and remaining acceptance checks (Chinese) |
| `pico-standalone/DESIGN_NOTEBOOK_EN.md` | Current independent Pico component | Reviewable algorithm/resource decisions and paused compute work (English) |
| `pico-standalone/DESIGN_NOTEBOOK_ZH.md` | Current independent Pico component | Reviewable algorithm/resource decisions and paused compute work (Chinese) |
| `pico-standalone/README.md` | Current independent Pico component | Setup, file roles and validation limits |
| `pico-standalone/README_EN.md` | Current independent Pico component | Setup, file roles and validation limits (English) |
| `pico-standalone/README_ZH.md` | Current independent Pico component | Setup, file roles and validation limits (Chinese) |
| `pico-standalone/dsp/README.md` | Current independent Pico component | Setup, file roles and validation limits |
| `pico-standalone/dsp/gap_dsp.c` | Current independent Pico component | Fixed HF2 matched filter, peak selection and arrival-consensus fit |
| `pico-standalone/dsp/gap_dsp.h` | Current independent Pico component | DSP result, workspace and phase-profiling interfaces |
| `pico-standalone/dsp/gap_fast_float.h` | Current independent Pico component | Binary32 scaling/rounding with library fallback |
| `pico-standalone/dsp/gap_integer_fft.h` | Current independent Pico component | Bounded integer FFT and optional verified fast arithmetic |
| `pico-standalone/dsp/gap_integer_tables.h` | Current independent Pico component | Read-only Q15 sine constants for the integer FFT |
| `pico-standalone/dsp/gap_tables.h` | Current independent Pico component | Compiled HF2 template spectrum and FFT constants |
| `pico-standalone/dsp/generate_tables.py` | Current independent Pico component | Reproduce fixed template and transform constants |
| `pico-standalone/firmware/BUILD.json` | Current Pico firmware release | Frozen source/artifact identity and build/deployment metadata |
| `pico-standalone/firmware/README_EN.md` | Current Pico firmware release | Setup, file roles and validation limits (English) |
| `pico-standalone/firmware/README_ZH.md` | Current Pico firmware release | Setup, file roles and validation limits (Chinese) |
| `pico-standalone/firmware/pico_gap_standalone-v0.2.elf` | Current Pico firmware release | Firmware executable/symbol artifact for debugging and resource analysis |
| `pico-standalone/firmware/pico_gap_standalone-v0.2.uf2` | Current Pico firmware release | Compiled firmware image; consult build identity before deployment |
| `pico-standalone/firmware/resource-audit.json` | Current Pico firmware release | Linker resource accounting; not measured runtime free memory |
| `pico-standalone/main.c` | Current independent Pico component | Pico capture, scheduling, DSP invocation and telemetry |
| `pico-standalone/sen0325_i2s.pio` | Current independent Pico component | PIO program for synchronous microphone I2S sampling |
| `pico-standalone/standalone_link.h` | Current independent Pico component | UART framing, CRC, ACK parsing, age and confirmation helpers |
| `pico-standalone/tests/dsp_harness.c` | Standalone host validation | Run portable C DSP on host PCM fixtures; no device access |
| `pico-standalone/tests/host_link_test.c` | Standalone host validation | 41 host checks of CRC, ACK parsing, bounds and age/confirmation |
| `pico-standalone/tests/observe_pnr_sensitivity.py` | Standalone host validation | Observe threshold sensitivity without changing production defaults |
| `pico-standalone/tests/run_offline_validation.py` | Standalone host validation | Compare C DSP with the retained PC reference on public fixtures |
| `pico-standalone/tests/test_analyze_link_trial.py` | Standalone host validation | Regression cases for link pairing, sessions and missing evidence |
| `pico-standalone/tests/test_main_communication.py` | Standalone host validation | Extract real Pico main functions for 107 mocked host assertions |
| `pico-standalone/tests/test_monitor_startup.py` | Standalone host validation | Check startup backlog/LF alignment and unmodified formal records |
| `pico-standalone/tests/test_reference_paths.py` | Standalone host validation | Verify portable reference discovery after repository cleanup |
| `pico-standalone/tools/analyze_link_trial.py` | Optional viewer and evidence tools | Pair TX, ESP fields and ACK observations without hiding gaps |
| `pico-standalone/tools/desktop.py` | Optional viewer and evidence tools | Optional radar/timing telemetry viewer; Pico computes direction |
| `pico-standalone/tools/desktop_control.py` | Optional viewer and evidence tools | Start, focus, validate and gracefully restart the local viewer |
| `pico-standalone/tools/monitor.py` | Optional viewer and evidence tools | Finite serial recording with explicit startup alignment |
| `references/README.md` | Supplied original reference | Setup, file roles and validation limits |
| `references/README.txt` | Supplied original reference | Setup, file roles and validation limits |
| `references/README_EN.md` | Supplied original reference | Setup, file roles and validation limits (English) |
| `references/README_ZH.md` | Supplied original reference | Setup, file roles and validation limits (Chinese) |
| `references/Tagalong_Project_Notes.docx` | Supplied original reference | Supplied original project/hardware reference; preserved in its original language |
| `references/Tagalong_Proposal.pptx` | Supplied original reference | Supplied original project/hardware reference; preserved in its original language |
| `references/hardware/MSM261S4030H0.pdf` | Supplied original reference | Supplied original project/hardware reference; preserved in its original language |
| `references/hardware/Pico-backside-user.jpg` | Supplied original reference | Hardware/reference image |
| `references/hardware/Pico-installed-user.jpg` | Supplied original reference | Hardware/reference image |
| `references/hardware/SEN0325-array-datasheet.pdf` | Supplied original reference | Supplied original project/hardware reference; preserved in its original language |
| `references/hardware/SEN0325-connector-user.jpg` | Supplied original reference | Hardware/reference image |
| `references/hardware/SEN0325-schematic.pdf` | Supplied original reference | Supplied original project/hardware reference; preserved in its original language |
| `reports/communication-2026-11-12/REPORT_EN.md` | Public stage evidence and figures | Measured stage report with comparisons and evidence limitations (English) |
| `reports/communication-2026-11-12/REPORT_ZH.md` | Public stage evidence and figures | Measured stage report with comparisons and evidence limitations (Chinese) |
| `reports/communication-2026-11-12/build_report.py` | Public stage evidence and figures | Reproduce public communication report figures from sanitized metrics |
| `reports/communication-2026-11-12/figures/communication_EN.png` | Public stage evidence and figures | Measured report figure |
| `reports/communication-2026-11-12/figures/communication_ZH.png` | Public stage evidence and figures | Measured report figure |
| `reports/communication-2026-11-12/metrics.json` | Public stage evidence and figures | Sanitized machine-readable measured results and limitations |
| `requirements.txt` | Project setup, documentation and integrity | Declared Python dependencies for this component |
| `tools/launch.cmd` | Local maintenance and verification | Shared runtime selection for the monitor entry scripts |
| `tools/refresh_catalog.py` | Local maintenance and verification | Generate bilingual catalogs and selected-file SHA256 checksums |
| `tools/verify_release.py` | Local maintenance and verification | Read-only release, hash, ZIP, link, privacy and build-identity audit |
