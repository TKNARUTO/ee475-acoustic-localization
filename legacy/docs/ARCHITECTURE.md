# Architecture and Implementation Map

## Present data path

```text
Phone WAV beacon
       | acoustic propagation
SEN0325: 6 outer microphones + 1 center
       | 4 parallel I2S data lines
Pico RP2040: PIO + DMA, 48 kHz
       | USB: validated 7-channel sample bursts
Windows application
       +-- target-band known-code matching
       +-- multi-pair direction estimator
       +-- validity gating and temporal filtering
       +-- radar-style bearing display / diagnostics / logs

Planned: bearing + validity -> ESP32 -> distance radar / steering / following
```

## Firmware and transport

`main.c` owns capture/control and USB output; `sen0325_i2s.pio` captures four simultaneous data bits; `tone_filter.h` supports the earlier narrowband diagnostic path. The current coded path requests 4,096 contiguous frames per burst, seven signed little-endian 16-bit channels, for 57,344 payload bytes. There are gaps between requested bursts; this is not continuous lossless USB streaming.

The ASCII `AUDIO` header includes frame count, sample rate, channel count, payload length, sequence, dropped-block count, RX-stall count, processing time and CRC32. The host checks the length, CRC32 and matching `AUDIO_END` trailer before processing. Invalid or late results are rejected. Coded capture keeps clocks running between bursts; STOP disables capture clocks. The supplied image runs from SRAM and does not program Flash.

## Beacon and direction processing

The default audible beacon occupies 0.9-3.9 kHz. A fixed-seed, band-limited periodic waveform repeats every 4,096 samples (85.333 ms). The 48 kHz, 16-bit phone WAV contains 144 periods (12.288 s) with short fades. Its left channel is silent and right channel carries the code to reduce simultaneous phone-speaker sources; the actual speaker route still depends on the player/device.

`beacon_dsp.py` matches the known template within the selected band. Current gates require a code peak-to-noise ratio of at least 14.5 dB, concentration of at least 0.18, and at least four matching microphones. A common-arrival window attenuates late reflections. The audible estimator combines up to 21 microphone pairs using PHAT weighting and a 360° search with several planar projection factors. Spatial score/margin checks and two consistent candidates precede accepted output. Strong signals use a shorter history; weaker signals retain more averaging.

`direction_estimator.py` contains the earlier narrowband phase estimator and persists front-reference/mirror settings. It is retained for diagnostics; it is not the default audible coded estimator. The 20.04-21.96 kHz experimental profile uses group delay across frequency to reduce carrier-phase ambiguity. Real high-frequency direction tests have not passed at this milestone.

The known code is a signal-selection mechanism, not secure source authentication. Same-code transmitters, strong reflections, near-field sources, moving sources and clock/device differences require additional testing.

## Desktop modules

| File in `SEN0325-Pico-Setup/` | Responsibility |
| --- | --- |
| `sen0325_launcher.py` | Pico discovery, RAM loading, serial worker, packet integrity and event queues. |
| `sen0325_simple_view.py` | English interface, diagnostics and trial logging. |
| `app_controls.py` | Independent capture/playback state and audio-profile selection. |
| `radar_canvas.py` | Bearing-only canvas, freshness checks and short visual transitions. |
| `beacon_dsp.py` | Beacon generation, matched detection and coded direction estimation. |
| `direction_estimator.py` | Geometry/calibration persistence and legacy phase estimator. |
| `runtime_tuning.py` | Capture wait, UI refresh and temporal-filter parameters. |
| `sen0325_view.py` | Shared level history and compatibility entry point. |
| `tracking_audio.py` | Earlier single-tone diagnostic audio helper. |
| `array_geometry.json` | Nominal geometry, front reference, mirror state and calibration fields. |

## Refresh behavior

The inter-capture wait is 5 ms instead of 120 ms. Actual burst processing and USB transfer make the acquisition loop much slower than either number alone. A 33 ms UI timer and 80 ms transitions improve visual continuity between measured estimates; they do not create new acoustic measurements. Invalid or stale estimates clear the arrow. The strong-signal filter uses two bursts and a 0.16 s smoothing constant; weaker signals use up to three bursts and 0.28 s smoothing.

## Planned embedded handoff

The ESP32 interface is not implemented. Agree on a message carrying sequence/timestamp, bearing relative to a calibrated front, validity and quality, with a timeout behavior, before connecting vehicle motion. Moving the estimator from the computer to the Pico or another embedded host is a separate implementation task.
