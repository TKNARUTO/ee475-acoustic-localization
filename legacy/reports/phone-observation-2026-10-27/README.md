# RX2 phone playback observation — 27 October 2026

This folder records a receive-only test of the 19–21 kHz LOCATE preset with firmware v0.6 / RX2. It is an observation checkpoint; no firmware, DSP thresholds, direction guards or GUI controls were changed.

## Test context

- Phone speaker playback: `01_LOCATE_20kHz_19-21kHz.mp3`.
- User-reported separation: less than 0.5 m; exact distance, motion and true bearing were not recorded.
- The user confirmed that phone audio paused or stopped sounding during the test. Pause timestamps are unknown. The whole-session no-code count must not be used as a receiver failure rate.
- Estimate window: 17:32:17–17:37:56, local time (UTC−07:00), 1,736 processing windows.
- A separate operator scan toggle paused scanning at 17:34:03.375–17:34:08.372. This is excluded from transport-failure interpretation.

## Findings and limits

Normal results arrived about every 188 ms. Median normal packet completion was 163.9 ms; median request-to-draw was 203.5 ms. The snapshot contains no packet-validation error, with reported dropped blocks and RX stalls both zero. These are pipeline measurements, not sound-onset-to-correct-bearing latency.

Of 666 windows with at least four code-matched channels, 434 failed relative-delay fitting, 126 awaited direction confirmation, and 106 emitted a direction. These are descriptive counts for this interrupted session. They do not establish sensitivity or angular accuracy.

A roughly 7.8 s run contained 41 consecutive code-hit windows and no accepted bearing. A later roughly 4.5 s run contained 24 consecutive accepted bearings. Direction output therefore remains intermittent even within code-matched periods. Phone pauses prevent a reliable interpretation of the overall no-code periods.

## Files

| File | Purpose |
| --- | --- |
| [OBSERVATION_ZH.md](OBSERVATION_ZH.md) | Chinese findings, timing interpretation, phase notes and next diagnostic scope. |
| [observation.json](observation.json) | Counts, timing summaries, selected runs, user corrections and frozen-log checksum. |
| [launcher-20261027-172051-289267.txt](launcher-20261027-172051-289267.txt) | Frozen receiver log through the snapshot cutoff; later activity is outside this report. |

No raw multichannel audio recording was successfully saved in this observation. Use the log to verify event timing and acceptance reasons. Resolving per-microphone waveform and relative-delay errors requires a separate controlled raw capture. RX2 firmware and USB/CRC benchmark evidence remain in [the latency reduction checkpoint](../../stages/04-latency-reduction/README.md).
