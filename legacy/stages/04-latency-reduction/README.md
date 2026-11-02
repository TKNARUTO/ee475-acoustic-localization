# RX2 — Lower Capture and Transfer Latency

EE475 / 27 October 2026 / Pico firmware **0.6-RX2**

RX2 reduces the normal wait for each seven-channel audio packet. It builds on RX1 packet recovery and targets the device-side costs identified by the delay investigation: USB transmission and firmware CRC calculation.

## Start and test

1. Connect the existing Pico/SEN0325 setup and open `EE475/Start-20kHz.cmd`.
2. Select **Start Scan** and loop `audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3` on the phone.
3. The computer remains receive-only. The matching MP3, 19–21 kHz band and Import Beacon workflow are unchanged.
4. To capture a physical trial, hold the phone still, open **Advanced**, enter the measured distance and select **Record 10 s**. Keep its physical side/orientation noted separately. Completed trials save metrics JSON and raw seven-channel NPZ under `SEN0325-Pico-Setup/logs/`.

The connected Pico already runs the selected firmware. The launcher recognizes old v0.5 firmware and upgrades it to the validated v0.6 image in RAM. BOOTSEL loading uses the same current image. RAM code is lost on power removal; use the existing launcher/BOOTSEL workflow again. No Flash payload was written during this work.

## Measured changes

Each benchmark below captured 100 ambient packets with the same 48 kHz / 4096-frame / seven-channel format. Startup cycles ≥450 ms are excluded from the steady packet metrics.

| Median measurement | Instrumented old configuration | Selected RX2 |
| --- | ---: | ---: |
| Firmware CRC calculation | 22.47 ms | 7.17 ms |
| Device payload transmission | 101.78 ms | 70.42 ms |
| Host request → packet validated | 208.42 ms | 164.48 ms |
| Host request → direction result queued | 222.67 ms | 176.61 ms |
| Consecutive request interval | 236.19 ms | 189.01 ms |
| Capture/estimation rate | 4.23 Hz | 5.29 Hz |

Packet wait fell about **21%**, and capture/estimation throughput rose about **25%** in these runs. The final GUI test accepted 91 ambient packets, passed all 21 checks, and observed **5.35 Hz** detection updates with **32.26 Hz** GUI refresh. Its steady request-to-draw-command median was **194.15 ms**; Tk drawing completion is not measured monitor presentation.

These are transport and software-cycle measurements. There was no new phone beacon playback or known-angle physical trial, so this checkpoint does not establish phone-to-correct-arrow latency or improved direction accuracy. Strong beacon DSP may cost more than ambient processing. The original confirmation, history and smoothing remain.

## Implementation

- USB software TX FIFO: **4096 bytes**; RX FIFO and endpoint transfer buffer: **512 bytes**. The full-speed USB endpoint packet size stays **64 bytes**.
- CRC-32 uses a 256-entry lookup table with the same polynomial, initial value and final inversion. CRC checks remain mandatory.
- Firmware reports per-packet capture, CRC and payload-send timings. The binary payload and exact `AUDIO_END seq=...` trailer remain compatible.
- Host recognizes v0.6 and performs a verified RAM upgrade when v0.5 is detected.
- Matching ELF and UF2 are installed together under `SEN0325-Pico-Setup/firmware/`.

A 1024-byte endpoint-buffer candidate was tested. Its whole-packet median was 163.09 ms versus 164.48 ms for 512 bytes: about 1.4 ms difference, with more RAM use. The smaller configuration was selected.

GPIO mapping, sample unpacking/channel order, array geometry, `highband_dsp.py`, smoothing, confirmation and UI source are preserved. No large-turn veto or forced 180° correction was added. Physical `group_delay_inconsistent` and reverse-bearing behavior still need the phone trial.

## Checks

- Three CRC vectors verified on the actual Pico against Python zlib: standard string, empty input, all 256 byte values.
- Five successful 100-packet benchmark runs, including old-firmware automatic upgrade. No packet-integrity errors, dropped buffers or RX stalls in these normal runs.
- Fourteen deterministic packet-reader/recovery checks and scan-control regression passed.
- Live CRC corruption and host-read-stall injection both rejected invalid packets and recovered; 46 good packets accepted. Error detection → next validated packet was 700 ms / 1,151 ms, excluding fault-detection waiting.
- Actual GUI: all 21 checks passed, including scan start/stop, import, seven channels, spectrum, waveform and layout.
- UF2 payload addresses verified as SRAM-only; installed ELF/UF2 match the selected build.

## Files

- [Progress notes in Chinese](PROGRESS_NOTES.md)
- [Detailed change notes](CHANGE_DETAILS.md)
- [Delay reduction report](../../reports/latency-reduction-2026-10-27/LATENCY_REDUCTION_ZH.md)
- Root JSON files: benchmark summaries, CRC/recovery/UI/upgrade checks and firmware metadata.
- `evidence/`: frozen launcher logs, including the rejected buffer-mismatch trial.
- `experiments/`: old and experimental RAM images; these are evidence, not normal launch targets.
- `backups/`: pre-RX2 project sources/image and instrumented bitwise-CRC source snapshot.
- `build-logs/`: compilation and RAM-loading logs.
- `FILE_INDEX.txt`: file-location index for this checkpoint.

The first USB candidate left the RX FIFO smaller than the endpoint transfer buffer and could not receive commands. TinyUSB's receive-space requirement was identified, the settings were coupled, and the corrected firmware was retested. That rejected image is retained only as development evidence; it is not the shipped image or an explanation of historical v0.5 packet faults.
