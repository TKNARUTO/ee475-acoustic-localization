# Pico standalone acoustic localization — setup and status

Updated 12 November 2026, through Flash trial 05 (no Pico USB reader). [中文](README_ZH.md). Current stage: **Pico v0.2-link_diag → ESP32 receiver v1.1**. Further FFT and dual-core optimization is paused; this stage keeps the existing boards and the tested FAST integer estimator while checking microphone → Pico → ESP32 communication. Pico captures SEN0325 audio, matches the fixed HF2 Gap beacon and computes bearing; the computer is an optional telemetry viewer. Motor control is outside this stage.

Read [the communication notebook](COMMUNICATION_NOTEBOOK_EN.md) for the current decisions, packet semantics, evidence and pending checks; [the design notebook](DESIGN_NOTEBOOK_EN.md) preserves computation history and the section 11 bandwidth budget. This is not a finished robot controller: the 0.2–0.5 s delay target remains unmet.

## Current evidence and deployment status

| Check | Observed result | Limit |
|---|---|---|
| Native Pico main / link / ESP32 checks | 107 / 41 / 57 assertions passed | Mocked/native tests do not establish physical timing or acoustic accuracy |
| Trial 01, background | 38/38 transmitted records matched ESP fields exactly; 37 later Pico ACK confirmations | The remaining ACK observation is at the recording boundary, not a proven lost or harmless packet |
| Trial 02, phone beacon | 33 exact matches from 34 Pico TX records; 32 later Pico ACK confirmations; 32 fits from 34 windows; all windows had 7 code-positive microphones | Startup output contained 4453 repeated-prefix observations and one malformed STAT record; the overall observation was **not passed** |
| Usable control targets | 0 in both trials | Result ages exceeded 500 ms; 750 ms confirmation and freshness rules were not relaxed |

Trial 02 remains not passed. After startup handling was changed, Flash trial 03 produced 37/37 exact matches, 37 CRC-valid ACKs and 36 later Pico ACK confirmations over 30 seconds, with zero parse errors, interior missing observations or field conflicts. Startup warmup captured 9063 bytes and aligned at LF after 1.125 seconds; no mid-recording deduplication was applied. Trial 04 used a software reboot and produced a new session with 14/14 exact matches, 14 CRC-valid ACKs and 13 later confirmations over 12 seconds. This is software-reboot recovery, not a physical power-cycle test. Trial 05 recorded only ESP COM6 for 12.109 s with no Pico USB reader: 15 continuous BEARING sequences 48–62 and 14 CRC-valid ACKs 49–62, with all observed bad/lines/ack_drop/usb_drop counters zero. It establishes continued transmission without a Pico reader, not physical USB disconnection or independent-power cold start. Warmed-up phone and physical cold-start tests remain separate checks.

Trials 01/02 used Pico RAM v0.2; trials 03/04 used Pico Flash v0.2. The RAM UF2 SHA256 is `7822b95524771d02305743715eeb17d09938065297edf0ed902e99ea9ddc8fb9`. The Pico Flash candidate `11958e9310926e856f01359c10c4832cffc046cb64a8edebe675b76e3984caa0` was written and verified with picotool `load -v`. ESP32 receiver v1.1 was installed for the trials. Its later desktop-sketch merged image `36610897ee2f78f5fe8153d043df68cbb00b5a7cf040c7d3475dc2b3d77cda6b` was also written and hash verified. Writing and verifying a binary does not establish acoustic accuracy or cold-start behavior.

## Actual platform and tool versions

| Component | Configuration verified for this stage |
|---|---|
| Pico target | Raspberry Pi Pico / RP2040, 120 MHz core0; `PICO_BOARD=pico`, `PICO_PLATFORM=rp2040` |
| Pico framework | **Native C11/C++17 with Pico SDK 2.3.1, not Arduino**; SDK commit `079c6f39023649b154152db30f1d781e884879bc` |
| Compiler actually used | Arm GNU Toolchain **14.2.Rel1** build arm-14.52; GCC/G++ **14.2.1** 20241119 |
| Build tools | CMake **4.4.4**; Ninja **1.13.2.git.kitware.jobserver-pipe-1** |
| Pico write/verify tool | picotool **2.3.1** |
| ESP32 board | **NodeMCU-32S / classic ESP32, not ESP32-S3**; FQBN `esp32:esp32:nodemcu-32s` |
| ESP32 editor/build | Arduino IDE **2.3.8**, Arduino CLI **1.4.1**, Boards Manager **esp32 by Espressif Systems 3.3.12** |
| ESP32 flashing tool | esptool **5.5.0** |
| Optional PC monitor | Python **3.12.4**, pyserial **3.5** |
| Local port observations | Pico Flash **COM8**, ESP32 **COM6**; earlier Pico RAM used COM5. Re-detect on another machine or after re-enumeration. |

Compiler versions were checked against the actual CMake build, not another GCC installation on PATH. Native C tests used Cygwin GCC 4.8.3; that is not the firmware compiler.

## Run and monitor

The published [Pico v0.2 Flash UF2](firmware/pico_gap_standalone-v0.2.uf2) has SHA256 `11958e9310926e856f01359c10c4832cffc046cb64a8edebe675b76e3984caa0`, matching the verified deployed image. Keep its [build/source identity](firmware/BUILD.json) and [resource audit](firmware/resource-audit.json) with the binary. The [ELF](firmware/pico_gap_standalone-v0.2.elf) is for debugging; the UF2 is the flashable artifact. This public image uses the explicit FAST options below, not W1C1.

Use the project-root `Start.cmd` to open/focus the **Pico Standalone Monitor**. `Update.cmd` validates local monitor sources and gracefully restarts its window; it does not download Git updates. Neither entry writes firmware or falls back to the old computer estimator. The outer EE475 directory retains its existing Chinese-named forwarder; this project root exposes only Start.cmd and Update.cmd.

The Pico firmware starts scanning on its own. The viewer can request Pause/Resume and set a **display-only** front reference. Closing the window leaves Pico running. Green arrows require a confirmed, fresh device result. Amber arrows are explicitly labelled diagnostic fits and are not valid control targets. The second chart displays measured Pico DSP phase time; this firmware does not stream the original seven-channel waveform to the viewer. The finite two-port monitor, rather than GUI automation, is used for the present communication trials; run only one reader per serial port.

Loop `audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3` or its WAV on the phone. This firmware recognizes that fixed template only. Arbitrary phone-file playback does not install a new template in Pico. Frequency, 48 kHz sampling and 4096-sample period remain unchanged.

## Wiring

| Pico | ESP32 NodeMCU ESP-32S | Direction |
|---|---|---|
| GP0, physical 1 | P16 / GPIO16 | Pico TX to ESP32 RX |
| GP1, physical 2 | P17 / GPIO17 | Pico RX from ESP32 TX |
| GND, physical 3 | GND | Common ground |

115200 8N1, 3.3 V logic. Keep the existing SEN0325 GP6–GP13 wires. Use each board's USB supply, with no board-to-board 3V3/5V/VIN wire. ESP32's separately printed RX/TX console pins are not P16/P17. Disconnect power before rewiring.

## Source and file roles

| File or directory | Role |
|---|---|
| `main.c` | Autonomous capture, timing, UART and bounded USB diagnostics |
| `sen0325_i2s.pio` | Preserved synchronous microphone sampling |
| `standalone_link.h` | CRC, ACK validation, actual measurement age and confirmation |
| `CMakeLists.txt` | RAM/Flash builds and optional integer FFT selection |
| `dsp/` | Portable C estimator, generated fixed reference and selectable FFT kernels |
| `tests/` | Native synthetic/recorded comparisons and threshold observations |
| `tools/desktop.py` | Optional radar and measured-phase viewer; no PC localization |
| `tools/desktop_control.py` | Local startup, focus and graceful update |
| `tools/monitor.py` | Finite receive-only diagnostic recording |
| `DESIGN_NOTEBOOK_EN.md` | User-reviewable engineering decisions and results |
| `COMMUNICATION_NOTEBOOK_EN.md` | v0.2 link decisions, diagnostic/control distinction, trial evidence and pending checks |
| `logs/` | Local runtime telemetry; excluded from public handoff |

The project [file catalog](../docs/FILE_CATALOG_EN.md) records the full inventory. Earlier mature software is preserved as [pico+computer combo sensoring version](../legacy/pico+computer%20combo%20sensoring%20version/README.md), plus a verified ZIP beside that directory. The compute checkpoint `pico-standalone-compute-checkpoint-2026-11-12` (external local archive, not shipped) separately preserves tested FAST candidates and the offline-only W1C1 experiment. These archives remain unchanged. The old combo launcher intentionally loads its v0.6 RAM capture image and performs localization on the computer; it is not the standalone viewer.

The authorized desktop sketch `sketch_nov12a` (local desktop copy) contains the frozen receiver's `.ino`, `gap_protocol.h`, `gap_diagnostics.h` and `gap_self_tests.h`, plus `sketch.yaml` selecting `esp32:esp32:nodemcu-32s` / COM6. Its original blank sketch was backed up in the private dated output directory. Independent compilation passed: 277624 program bytes and 22932 global-data bytes. The merged firmware was subsequently written and verified; trial 03/04 used it. This is an editable receiver copy, not a motor-controller merge; the EE474 source was not modified. COM port assignments can change after reconnecting.

## Build and validation state

Use Pico SDK and an ARM toolchain. `PICO_NO_FLASH=ON` builds a nonpersistent SRAM test image; the normal build uses Flash XIP. `GAP_INTEGER_FFT=OFF` preserves the float baseline; enable it explicitly for the validated integer candidate. Do not infer which binary is running from the current source alone: keep the UF2 hash, source snapshot and telemetry backend together.

The communication-stage backend is selected with `GAP_INTEGER_FFT=ON`, `GAP_INTEGER_FAST=ON`, `GAP_WHITEN_FLOAT=OFF` and `GAP_MAG_CACHE=OFF`. Use separate RAM and Flash build directories. W1C1 flags and a newer source file do not establish that the experimental candidate is running.

The first 120 MHz float RAM trial measured roughly 2.73 seconds of DSP per window and 2.83 seconds per result. About 90% of DSP wall time was FFT. FAST integer arithmetic was subsequently board tested: the earlier phone communication trial 02 measured median DSP 789.160 ms, cycle 884.558 ms and measurement age 834 ms. Background trial timing was lower and is not an equal-input speed comparison. Further computation work is paused; W1C1 remains offline verified only, and dual-core remains a design without implementation.

The estimator uses a shared bounded workspace and is not reentrant. Only core0 is currently used. Linker heap capacity and static function frames are not measured runtime heap/stack high-water values. A future control loop needs deadline measurements and feedback integration, not just spare RAM.

Native verification covers synthetic directions, large turns, saved recordings, background, wrong codes and weak signals. Integer-versus-float decisions agreed for 580 windows; the maximum bearing difference was 0.036026 degrees. The original 12.5 dB detector still accepts some deliberately constructed same-band wrong codes. Changing FFT arithmetic does not solve that limitation. Known-angle physical accuracy remains a separate acceptance test.

## Interface and recovery

USB emits `PICO_GAP_STANDALONE ...`, `GAP {...}`, `PROFILE {...}` and requested `STATUS {...}` lines. GAP distinguishes `fit_valid`, `confirmed` and final `valid`. v0.2 adds metadata for the actual successful UART transmission (`tx_result_seq`, `tx_age_ms`, `tx_valid`, `tx_angle_cdeg`, `tx_quality`) and the later matched B acknowledgement (`ack_seq`, `ack_roundtrip_us`, `ack_status`). Failed writes do not manufacture a successful TX record. ACK roundtrip includes foreground parsing time; it is not isolated wire latency. Window timing, DSP age and transport observations remain separate quantities. The USB path is designed not to wait for a computer; trial 05 observed continued output without a Pico USB reader; physical power cycling remains a separate check.

UART uses the [gap receiver protocol](../esp32-link/gap_receiver/README.md): fresh session per boot, sequence numbers, CRC16, explicit invalid values, ACK and 500 ms expiry including a 20 ms transport allowance. Age is measured from the window center. Confirmation requires two code hits separated by less than 750 ms. Large changes in bearing are not rejected solely because of their size.

An eight-field B packet may retain a finite diagnostic angle/quality with `valid=0` when the fit is stale or unconfirmed. No fit, capture override or nonfinite data produces zero diagnostic fields. ESP32 prints the received `raw_cdeg`, `raw_q` and `source_age_ms` independently of its `target_valid`; invalid data cannot become a steering command. Zero degrees is also a legitimate bearing: B alone does not reveal `fit_valid`, confirmation or the detailed failure reason. Match Pico USB diagnostics by result/UART sequence when investigating those details. H/P traffic does not renew an old direction, and a handshake ACK does not overwrite the last B-ACK diagnostic metadata.

Before deployment, the existing ESP32 Flash was fully read and verified over 4 MiB. The Pico range 0x10000000–0x10200000 was saved and verified. These original device images stay in local dated outputs, outside the shareable project. The temporary ESP32 application is receive/ACK-only. A RAM candidate can be replaced without writing Pico Flash; the communication Flash image is now verified and its software reboot was observed; an independent-power physical cold start is still a separate acceptance test.

## Rebuild and evidence portability

Run from the project root with the verified tools available. Replace the SDK directory placeholder with your installation; use separate RAM and Flash build directories:

```powershell
cmake -S pico-standalone -B build/pico-flash -G Ninja -DPICO_SDK_PATH="<pico-sdk-dir>" -DPICO_BOARD=pico -DPICO_PLATFORM=rp2040 -DPICO_NO_FLASH=OFF -DGAP_INTEGER_FFT=ON -DGAP_INTEGER_FAST=ON -DGAP_WHITEN_FLOAT=OFF -DGAP_MAG_CACHE=OFF
cmake --build build/pico-flash
arduino-cli compile --fqbn esp32:esp32:nodemcu-32s esp32-link/gap_receiver
```

These commands build; they do not deploy. The equivalent Chinese documentation is [README_ZH](README_ZH.md), [communication notebook](COMMUNICATION_NOTEBOOK_ZH.md) and [design notebook](DESIGN_NOTEBOOK_ZH.md).

Raw logs, recordings and device backups are **local evidence, not shipped**. Public summaries are planned at `reports/communication-2026-11-12/`, containing `REPORT_EN.md`, `REPORT_ZH.md`, `metrics.json` and `figures/`. Public documents use portable relative identifiers, not personal absolute installation paths.

## Public replay after repository cleanup

The shareable runner was rechecked against the retained mature PC reference using `--skip-real`: **187 windows, 29 checks, 27 passed and 2 known wrong-code rejection failures**. The groups are 144 circle, 37 rejection, 3 repeated wrong-code and 3 large-turn windows. The rejection group accepted 1/37 negative inputs; the repeated wrong-code group accepted 3/3. All four groups had zero C-versus-Python-arrival validity mismatches. Overall acceptance is therefore not passed.

This command used the default **float** source build, not the deployed FAST hardware image, and omitted private recordings. It tests public reproducibility and preserves the known detector limitation; it is not a new board-speed or physical-accuracy measurement. Five reference-path checks passed. Production PNR remains 12.5 dB.

```text
python pico-standalone/tests/run_offline_validation.py --skip-real --gcc <host-gcc> --output <external-output>
```

The default reference is `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup`; `--reference-app` can override it. Older standalone experiments and private compute checkpoint are maintained externally, not advertised as active files in this public tree.

## Reproduce host communication checks

Use a **host** GCC (the recorded test environment used Cygwin GCC 4.8.3), not the ARM cross-compiler. From the project root:

```powershell
python pico-standalone/tests/test_main_communication.py --gcc "<host-gcc-executable>" --output-dir "<external-test-output>/main"
# Ensure the host compiler's runtime/DLL directory is on PATH when running its executable.
& "<host-gcc-executable>" -std=c11 -O2 -Wall -Wextra pico-standalone/tests/host_link_test.c -o "<external-test-output>/host_link_test.exe"
& "<external-test-output>/host_link_test.exe"
```

Create the external output directory first. The Python runner discovers the current Pico source relative to itself, adds the compiler directory to its child-process PATH, and rejects an output directory inside the project. It extracts the real main functions rather than copying their logic; only UART/time/USB are mocked. Re-run results: **107 main assertions passed**, maximum tested GAP line **699 bytes**; **41 link checks passed, zero failures**. No DSP kernel, serial port or board was used. Compiler output and source hashes are written outside the project; native timings are not Pico timings.

## First installation

See [persistent firmware installation](firmware/README_EN.md) for BOOTSEL/RPI-RP2 or picotool loading, backup requirements and the exact deployed UF2. The Windows launcher never installs firmware.
