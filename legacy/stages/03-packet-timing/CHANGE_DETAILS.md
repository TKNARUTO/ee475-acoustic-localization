# RX1 Change Details

27 October 2026. Host transport and observability only.

## Application sources

| File in SEN0325-Pico-Setup | Change | Reason |
| --- | --- | --- |
| `raw_packet.py` | New exact-length packet reader, partial-line accumulation, explicit fault categories, segmented high-resolution timings, cancellation and bounded STOP/drain/resynchronize helper | Separate packet failures and recover without accepting corrupt or misaligned samples |
| `sen0325_launcher.py` | Calls packet reader; writes `# PACKET`, `# PACKET_ERROR`, `# PACKET_CANCEL`, `# RECOVERY`; performs local recovery; attaches pipeline timings to estimates | Preserve evidence at the failure boundary and bypass fixed reconnect delay for isolated recoverable faults |
| `sen0325_simple_view.py` | Logs one `direction_render` event for each newly consumed timed result after drawing commands | Measure result queue and UI work separately from acquisition/DSP |

`time.perf_counter()` measures elapsed durations. Existing `time.monotonic()` timestamps remain for freshness checks; their Windows resolution was about 15.6 ms on this machine. The two clock domains are stored under distinct field names and must not be subtracted from each other.

The request timer starts just before sending RECORD. Estimator initialization can occur before it. `dsp_ms` surrounds the estimator; `postprocess_ms` covers signal-scope and channel summaries. `capture_cycle_ms` is retained for historical compatibility. `queue_to_draw_ms` ends after drawing commands, without a forced Tk update or physical display measurement.

## Recovery behavior

1. Read up to 4096 × 7 × 2 = 57,344 bytes in accumulated short reads. Do not decode binary audio as text.
2. Require the specified sample format, exact byte count, CRC and matching `AUDIO_END seq=...` before DSP.
3. On a packet fault, emit invalid `capture_gap`, clear estimator history, send STOP and drain residual data. Retry STOP every 200 ms while draining, with a 1.2 s overall bound.
4. Resume only after STOP acknowledgement. A new RECORD then uses the firmware's existing 500 ms warm-up.
5. Escalate to the existing outer reconnect path if synchronization cannot be established or faults repeat three times consecutively. Serial-port errors also retain that path.
6. Treat scan/profile/connection cancellation separately from packet corruption. A cancelled burst cannot update the bearing.

Header timeout remains 4 s; trailer timeout remains 1 s. Payload has a 4 s total limit and a new 600 ms no-progress limit. Individual serial timeout is temporarily 20 ms and is restored after reading/recovery. These values are transport limits, not limits on source direction or angular motion.

The first live stall test showed that one STOP request was insufficient under stalled reception. The passing revision retries while draining and was rerun against both injected faults. The initial failed run is retained under `evidence/` so this boundary is not lost.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Binary framing, fragmentation, short payload, wrong CRC, trailer/header failures, cancellation, lost STOP acknowledgement, bounded recovery failure | `packet-fault-validation.json` | 14 checks passed |
| Scan-only controls; stale burst cancelled after Stop | `controls-validation.json` | Passed; no playback |
| Actual Pico, one CRC bit flip and one host-side read stall | `hardware-recovery-validation.json` | 2 faults rejected/recovered, 36 good packets, no outer-session ERROR |
| Actual GUI/Pico start/stop/import, seven channels, scope and layout | `ui-validation.json` | All 21 checks passed; 72 ambient packets |
| Components outside scope | `preserved-components.json` | `main.c`, high-band DSP and RAM UF2 hashes unchanged |

The updated GUI timing run includes intentional stop/profile changes. A sequence gap caused by a cancelled packet is distinct from a corrupt accepted packet. Baseline and updated runs differ in duration, GUI activity and system load, so their median differences are not a controlled throughput benchmark.

## Unresolved

This checkpoint does not identify which physical/firmware/USB event caused the two historical packet faults. It improves the recovery and the evidence available if they recur. It also does not resolve 20 kHz geometric-delay inconsistency, verify true bearing, improve distance acceptance or change phone output strength. The user deferred a new phone playback trial.
