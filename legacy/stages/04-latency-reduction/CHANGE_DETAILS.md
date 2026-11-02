# RX2 Change Details

27 October 2026. Firmware 0.6-RX2 and host loading compatibility.

## Sources

| File under SEN0325-Pico-Setup | Change |
| --- | --- |
| `CMakeLists.txt` | Configures TinyUSB software buffers: TX FIFO 4096, RX FIFO 512, endpoint transfer buffer 512; validates supported sizes and TX ≥ endpoint; embeds firmware version |
| `Build.ps1` | Defaults to selected 4096/512 buffers; exposes named build parameters for reproducible baseline/candidate comparisons |
| `crc32_fast.h` | New 1024-byte CRC lookup table and CRC-32/ISO-HDLC implementation, zlib-compatible |
| `main.c` | Uses fast CRC; records capture/CRC/TX durations; appends optional timing metadata; adds stopped-state CRC32CHECK diagnostic; identifies as v0.6 |
| `sen0325_launcher.py` | Recognizes v0.6; detected v0.5 triggers verified RAM-only upgrade after releasing the serial port |
| `firmware/` | Replaces both default UF2 and matching ELF; adds firmware notes |

`highband_dsp.py`, `runtime_tuning.py`, geometry, UI source and sample-unpacking/channel-order functions were compared against the backup and are unchanged. No beacon audio was regenerated.

## Timing boundaries

`capture_us` measures firmware RECORD command handling to completion of the fourth raw block, before CRC. It includes warm-up, block alignment, unpacking and scheduling. DMA clocks keep running between requests, so the first selected block can contain samples preceding RECORD; this value is not exactly the duration of a newly started 4096-sample window.

`crc_us` surrounds firmware CRC calculation. `tx_us` surrounds payload fwrite/fflush and is device-side send work; it is not a physical USB wire latency measurement. The unchanged `AUDIO_END seq=...` line closes the packet. `AUDIO_TIMING` follows and is normally collected while waiting for the next header, so the final accepted packet may lack its device timing in the host log. Benchmarks match timing lines by sequence.

Host timings continue to use RX1 high-resolution instrumentation. Benchmark summaries exclude startup packets ≥450 ms and only pair consecutive sequence numbers for request-interval statistics. All firmware durations are converted to milliseconds in `metrics_ms`.

## USB configuration requirement

The installed Pico SDK 2.3.1 configuration defaults to 64-byte full-speed CDC FIFO/transfer buffers. TinyUSB arms a receive transfer only when RX FIFO free space can accommodate the transfer buffer. Therefore RX FIFO must grow with the endpoint transfer buffer; changing only TX and endpoint buffers leaves command reception unarmed.

This requirement was found by the first candidate's write timeouts, confirmed in installed `tinyusb/src/class/cdc/cdc_device.c`, corrected, then validated on hardware. The SDK descriptor still defines `USBD_CDC_IN_OUT_MAX_SIZE` as 64. No SDK source or full-speed descriptor was modified.

The 1024-byte endpoint candidate was not selected: its approximately 1.4 ms whole-packet median difference did not justify the extra memory and configuration change in this checkpoint. The selected build contains 113,512 text bytes and 138,104 BSS bytes as reported by arm-none-eabi-size; linker symbols leave 14,624 bytes between `__end__` and `__HeapLimit`. SRAM address bounds and successful RAM loading were separately checked.

## CRC and integrity

Polynomial 0xEDB88320, initial 0xFFFFFFFF and final XOR 0xFFFFFFFF are preserved. Actual Pico results match independent zlib expectations:

| Input | CRC |
| --- | --- |
| 123456789 | CBF43926 |
| Empty | 00000000 |
| Bytes 00 through FF | 29058C73 |

Every accepted live packet still requires exact length, matching CRC and matching trailer. RX1 short-read accumulation, cancellation, bounded resynchronization and outer reconnect fallback remain in force. The accelerated build passed both injected corruption and stalled-read recovery.

## Validation sources

- `tests/benchmark_latency.py`: bounded live capture and read-only log summarization, with matched device timings and real header health counters.
- `tests/verify_crc32_hardware.py`: actual firmware vectors, with bounded wait for USB re-enumeration.
- `tests/verify_packet_recovery_hardware.py`: adds an output-folder option and records the actual firmware banner so old stage evidence remains intact.
- Existing packet/control checks and the actual 20 s GUI smoke check were rerun. All 21 GUI checks passed; 91 packets, no callback errors.
- `auto-upgrade-validation.json` confirms legacy detection, RAM loading, v0.6 identification and 100 subsequent accepted packets.

The benchmark variants were run on the same connected hardware with matching sample parameters. Development builds overlapped some exploratory runs; exact host timing differences are not a controlled acoustic experiment. The separate final run confirmed about 164 ms whole-packet latency. No fresh phone or known-angle trial was performed, so direction accuracy, range, strong-beacon DSP cost and sound-to-correct-arrow latency remain outside this acceptance.
