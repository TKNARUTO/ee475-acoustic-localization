# EE475 Weekly Update — Acoustic Localization

**Project:** Tagalong Following Robot  
**Week ending:** 17 October 2026  
**Assigned subsystem:** SEN0325 microphone array and Raspberry Pi Pico  
**Milestone:** Audible-beacon bench prototype; desktop v0.7 / Pico firmware v0.5

## Summary

This week, we established and tested the acoustic sensing path from the SEN0325 6+1 microphone array through the Raspberry Pi Pico to a Windows radar-style direction display. We moved from basic microphone-level tests and unstable single-tone phase estimates to a known coded audible beacon with multi-microphone direction estimation. The audible prototype is ready for further controlled testing; complete robot following and reliable inaudible operation have not been demonstrated.

## Work completed

- Connected the array to the Pico and implemented seven-channel synchronous 48 kHz acquisition using PIO and DMA.
- Implemented USB burst transfer with length, sequence and CRC32 checks, plus dropped-block and RX-stall reporting. Preserved a RAM-only loading workflow.
- Generated transferable phone beacon WAV files and added target-band code matching to reject signals that do not match the selected beacon.
- Added multi-pair SRP-PHAT direction estimation for the audible beacon, consistency checks, temporal filtering, and front-reference/mirror controls.
- Built a simplified 2D radar-style interface with independent receiver and sound-playback switches, seven-channel diagnostics, and distance-tagged trial recording.
- Reduced inter-capture waiting and improved visual refresh. The controlled live loop-timing benchmark increased from 2.92 to 4.57 Hz (about 56.6%); the display timer targets about 30 frames/s.
- Prepared an English interface, project README, organized folders, selected validation evidence and an English/bilingual weekly handoff package.

## Results and evidence

| Evaluation | Result | Scope |
| --- | --- | --- |
| Stationary audible-beacon bench trial | 18/18 evaluated stable playback windows had accepted bearings; 0/6 evaluated off windows did | Computer speaker; true angle and distance were not measured. |
| Unrelated 1 kHz tone | 0/19 evaluated tone-on windows matched the code or gave a valid bearing | One interference case, not a general rejection guarantee. |
| Live timing comparison | Median loop interval decreased from 343 to 219 ms; zero reported drops/RX stalls | No beacon playback; timing/integrity only. |
| Synthetic filter-response comparison | 0°→45° settling within ±5° improved from 1.0 to 0.4 s at the same 5 Hz input rate | Generated samples; not a physical tracking response measurement. |
| High-frequency experiment | Code matched in 19/19 evaluated playback windows, but 0/19 valid directions | Inaudible direction finding remains unsuccessful. |

The user reported that the audible version worked better on the intended Samsung S25 Ultra, while the inaudible version did not work. This feedback has not yet been converted into a controlled distance/angle acceptance test. Detailed reports are included under `reports/validation/`.

## Challenges and current limits

Single-tone phase estimates were often inconsistent, particularly as distance and reflections increased. Coded detection and multi-pair processing provide a better test baseline, but long-range robustness and real angular accuracy remain unverified. Direction is currently computed on the Windows host. The Pico/ESP32 interface, distance-radar alignment and motor-control loop have not been integrated. The radar-style rings indicate no measured range.

## Next steps

1. Measure bearing error and valid-output rate at marked angles and distances with the S25 Ultra, including trials beyond 1 m.
2. Calibrate orientation/timing and test reflections, unrelated audio and source movement.
3. Agree with the ESP32 team on bearing, validity, quality and timeout fields, then integrate the radar/steering loop.
4. Continue high-frequency work separately after the audible baseline is characterized.

## Short update for a meeting

We completed a working bench prototype for our SEN0325/Pico acoustic subsystem. It captures seven microphone channels, identifies a coded audible phone beacon, and displays an estimated bearing on a simplified radar-style interface. We also added packet-integrity checks, diagnostic logging and independent playback controls, and improved the measured acquisition-loop rate from about 2.9 to 4.6 Hz. The next priority is controlled angle-and-distance testing and the ESP32 handoff. Inaudible localization and complete vehicle following are still open.
