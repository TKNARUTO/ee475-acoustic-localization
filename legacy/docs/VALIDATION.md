# Validation Summary and Known Limits

Evidence below comes from saved reports produced during development. Bench results, simulation and user feedback are reported separately. This weekly packaging changes interface text and file organization; it does not improve the acoustic algorithm or create new physical accuracy measurements.

## Saved evidence

| Check | Result | Evidence in `reports/validation/` | Interpretation |
| --- | --- | --- | --- |
| Audible right-channel beacon, stationary computer-speaker bench trial | 18/18 evaluated stable playback windows produced accepted directions; 0/6 evaluated off windows did | `beacon-hardware-coded-audible-right-only.json` | Successful detection and direction output in one trial; source angle/distance unknown. Not angular accuracy or phone range acceptance. |
| Unrelated 1 kHz tone | 0/19 evaluated tone-on windows matched the code or produced a valid direction | `beacon-hardware-coded-audible-negative-1000hz.json` | Rejection of this interferer only; not general immunity to speech, music or all electronic noise. |
| High-frequency right-channel experiment | 19/19 evaluated playback windows matched the code, but 0/19 gave valid directions | `beacon-hardware-coded-ultrasonic-right-only.json` | Code detection did not establish localization. Group-delay consistency failed. Inaudibility was not measured. |
| Controlled live loop-timing comparison, no beacon playback | Median 2.915 to 4.566 Hz; 343 to 219 ms interval; zero reported drops/RX stalls in both stages | `refresh-rate-benchmark.json` | Approximately 56.6% higher loop rate. Does not prove moving-target rate or range. |
| Synthetic known-angle signals with noise and delayed reflection | 12 cases across two profiles passed; maximum simulated error about 0.36°; four negative input types rejected per profile | `beacon-model-validation.json` | Mathematical/model regression only. Physical angular accuracy remains unmeasured. |
| Synthetic 0° to 45° step at the same 5 Hz input cadence | Settling within ±5° improved from 1.0 s to 0.4 s | `refresh-response-validation.json` | Filter comparison on generated samples; not a measured phone response time. |
| Independent UI controls | Radar/playback combinations, playback failure and late-burst rejection passed | `simple-controls-validation.json` | Functional control behavior with silent playback test double. |

Earlier `simple-ui-smoke-test.json` records a real-Pico interface run with 38 raw bursts, all seven channels, 19 passing checks and no callback errors. The English packaging has its own layout/control check, recorded separately as `english-ui-validation.json`; it must not be presented as a new acoustic bench test.

The user reported that the audible version was usable on the intended phone and that the inaudible version did not work. This is qualitative feedback, without a recorded ground-truth angle or distance.

## RAM image integrity

The supplied firmware is v0.5; the desktop application is v0.7. The image has 421 payload blocks, all within SRAM from `0x20000000` to `0x2001a500` exclusive, with zero Flash payload blocks. The validated SHA256 is:

```text
b10c5203c44cb7dff7ba48007f787e13fe8327fa6068835a0d74e92aa9e4350c
```

The weekly packaging preserves the validated UF2 and phone WAV bytes. Original proposal and project notes are also preserved byte-for-byte. See `reports/packaging-validation.json` for the final packaging checks and `reports/pre-packaging-manifest.json` for pre-change hashes.

## Outstanding acceptance work

1. Measure angular error against physical ground truth, including left/right orientation and per-channel timing/geometry calibration.
2. Establish valid-output rate and error versus measured distance, especially at and beyond 1 m, using the Samsung S25 Ultra.
3. Test reverberation, unrelated speech/music, multiple sources, moving sources and device/player frequency response.
4. Resolve the high-frequency direction failure before claiming inaudible following; hearing and speaker behavior also require measurement.
5. Define start/stop/lost-target behavior and the Pico-to-ESP32 protocol; integrate the distance radar, steering and vehicle safety logic.
6. Decide where standalone direction estimation will run. Current results require the Windows computer.

Archived evidence may contain Chinese text and historical absolute paths. It is retained as original provenance, not rewritten as new measurements. SDKs, external runtimes and historical build caches are excluded from the distributable weekly archive.
