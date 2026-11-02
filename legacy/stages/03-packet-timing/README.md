# RX1 — Packet Timing and Recovery

EE475 / 27 October 2026 / host application update / Pico firmware v0.5

This checkpoint makes packet interruptions easier to diagnose and recovers from isolated invalid packets without the previous full-session retry delay. The selected beacon remains the 20 kHz preset, spanning 19–21 kHz. Physical bearing stability remains an open task.

## Run

1. Connect the existing Pico and SEN0325 wiring. Close other serial monitors.
2. Open `EE475/Start-20kHz.cmd`, then select **Start Scan**.
3. Loop `audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3` on the phone. Computer playback is not implemented.
4. For a later diagnosis trial, hold the phone still about 0.5 m from the array. Open **Advanced**, enter the measured distance and select **Record 10 s**. Keep the phone fixed until recording finishes. Completed trials save JSON metrics and a seven-channel raw NPZ in `SEN0325-Pico-Setup/logs/`.
5. Record which physical side the phone is on. Do not use Set Front during the diagnostic recording: an arbitrary new reference cannot establish true bearing accuracy.

No new phone playback trial was performed at this checkpoint: the user deferred it. The application has been reopened and left connected with scanning off.

## What changed

- High-resolution timings distinguish command write, header wait, payload read, host CRC, trailer, DSP, postprocessing and queue-to-draw work.
- Partial text lines survive short serial timeouts. Payload reads accumulate until the exact expected length; CRC and matching trailer remain mandatory.
- Error records distinguish a short payload, wrong CRC, malformed header, missing trailer and cancellation. They include byte counts, sequence and available checksum information.
- A failed packet is discarded. The host sends STOP, drains the remainder and requires a STOP acknowledgement before another capture. STOP is retried every 200 ms while draining, within a 1.2 s recovery deadline.
- An idle payload is detected after 600 ms without progress, with the original 4 s overall payload deadline retained. Individual reads use 20 ms timeouts so stop/reconnect/profile changes can be noticed promptly.
- Failed resynchronization, three consecutive packet faults or a real serial-port error still use the outer reconnect path. Isolated recoverable packet faults bypass its fixed 3 s retry wait.

The direction estimator, geometry, code thresholds, two-candidate confirmation, phone files and firmware are unchanged. Large-angle jump suppression and the hard dual-estimator veto remain removed. This update does not claim to fix `group_delay_inconsistent` or sudden reverse bearings.

## Measured results

The live GUI test accepted 72 ambient packets and passed all 21 UI checks. Seven channels, receive-only operation, import, start/stop and the two signal plots were checked. Observed GUI refresh was 32.26 Hz and capture/estimation rate 4.57 Hz. There was no matching phone beacon during this test.

| Current GUI measurement | Median | P95 |
| --- | ---: | ---: |
| RECORD write → header complete | 104.27 ms | 114.14 ms |
| Header complete → payload complete | 99.36 ms | 102.57 ms |
| Host CRC calculation | 0.043 ms | 0.071 ms |
| Request → packet validation complete | 201.56 ms | 215.72 ms |
| DSP, ambient input | 4.33 ms | 6.63 ms |
| Result queue → draw commands complete | 19.95 ms | 45.86 ms |
| Request → draw commands complete | 236.29 ms | 265.19 ms |

Packet timing excludes startup cycles ≥450 ms. The request-to-draw figures include startup in the underlying sample set; their maximum is reported in JSON. Drawing completion means Tk drawing commands have been issued, not measured monitor presentation. These are request-cycle measurements, not phone-to-correct-arrow latency. Header wait includes device acquisition, scheduling, firmware work and header delivery. The 4096-frame sample window alone is 85.33 ms.

Live fault injection accepted 36 good packets while deliberately corrupting one host-side payload byte and suppressing reads for one payload. Both invalid packets were rejected and both recovered without reopening the serial port:

| Injected fault | Error detected → next validated packet |
| --- | ---: |
| CRC bit flip | 737 ms |
| Payload stall | 1,188 ms |

These times include restarting capture with the existing 500 ms firmware warm-up. They do not include the time spent detecting the injected fault. This validates recovery behavior; it does not prove the cause of the two historical packet failures or establish physical direction accuracy. Normal capture latency remains approximately 0.2 s per packet.

## Files and evidence

- [Chinese follow-up report](../../reports/delay-followup-2026-10-27/DELAY_FOLLOWUP_ZH.md)
- [Stage progress notes](PROGRESS_NOTES.md)
- [Detailed source changes](CHANGE_DETAILS.md)
- `packet-fault-validation.json`: 14 deterministic framing/error/recovery checks.
- `controls-validation.json`: scan-only controls and cancellation of a stale burst.
- `hardware-recovery-validation.json`: live Pico fault injection, timings and log path.
- `ui-validation.json`, `updated-ui-timing.json`: real GUI and segmented timing evidence.
- `high-resolution-baseline.json`: 103 complete ambient packets before recovery changes.
- `host-baseline.json`: earlier 145-packet run; coarse Windows clock, retained for provenance.
- `preserved-components.json`: unchanged DSP, firmware source and UF2 hashes.
- `evidence/`: frozen copies of the relevant append-only launcher logs.
- `before-packet-timing.zip`: selected sources/docs/UF2 before RX1.
- `instrumentation-only.zip`: measured host instrumentation before recovery changes.

## Next checkpoint

Use the same phone file and save raw 20 kHz audio at fixed positions before changing direction estimation. Check pair-delay cycle consistency, center-channel bias, channel frequency response and reflections. A later moving-phone trial must allow real large turns. Do not treat a front-offset calibration or an arbitrary 180° flip as evidence that random reverse jumps have been solved.
