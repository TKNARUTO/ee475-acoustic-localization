# Retained computer + Pico sensing template

This is the final archived desktop-computation baseline. The phone plays HF2 gap audio, SEN0325 senses it, Pico captures seven channels and Windows estimates/displays bearing. Current independent Pico/ESP32 work is outside this template.

```mermaid
flowchart LR
 Phone[Phone playback] --> Array[SEN0325 array]
 Array --> Pico[Pico synchronous capture]
 Pico -->|USB PCM + CRC32| PC[Windows direction calculation]
 PC --> View[Direction and signal plots]
```

## Start

1. Extract the entire ZIP to a writable folder, preserving relative paths.
2. Follow [Windows setup](docs/SETUP_WINDOWS_EN.md), then [the wiring table](docs/HARDWARE_EN.md).
3. Connect the intended Pico. If necessary, hold BOOTSEL while connecting USB to expose RPI-RP2. The retained launcher validates and loads the supplied RAM image.
4. Open `一键启动.cmd` and select **Start Scan**. `Update.cmd` checks and restarts this local receiver; it does not download updates or launch the new standalone program.
5. Loop the matching [HF2 gap audio](audio/phone/HF2-gap-test/README_EN.md) on the phone. The computer remains receive-only.

## Firmware provenance

The runnable UF2/ELF pair is **v0.6-RX2**. UF2 SHA-256: `76470847618d44065001eba3615cf49e19e858a27839dd09543700e7d8471151`. Its payload targets SRAM only: **power loss requires reloading**.

Adjacent `main.c`, `CMakeLists.txt` and `link_frame.h` are **v0.8-BRIDGE development source**, not verified build sources for the supplied v0.6 image. Running Build.ps1 does not establish a v0.6 reproduction. Preserve the runnable pair for baseline comparisons. Optional bridge configuration remains `enabled: false`; no motor control or independent Pico estimator is included.

## Interpretation and handoff

HF2 gap uses 18–22 kHz, 48 kHz sampling, 4096 samples per period and 2048 active + 2048 silent samples. The silent half is intentional. A held arrow is not a new measurement; radar rings do not measure range. High-frequency output, audibility, reflections and orientation must be tested physically. Large genuine turns remain allowed.

See [receiver use](docs/USER_GUIDE_EN.md), [validation](VALIDATION_EN.md), [file catalog](FILE_CATALOG_EN.md), [agent handoff](AGENTS_EN.md) and [platform requirements](PLATFORM_EN.md). SOURCE_MANIFEST.json preserves original source provenance and this documentation revision; SHA256SUMS.txt covers every file except itself. Private recordings, logs, custom imports, keys and toolchains are excluded.

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
