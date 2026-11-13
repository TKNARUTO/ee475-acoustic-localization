# HF2 Gap portable DSP

Initial C implementation, 12 November 2026. This directory contains the independent estimator; board capture, sample age, confirmation, UART and USB belong to its caller. Native replay and on-board timing must be checked before deployment or performance claims.

## Fixed input and output

`gap_estimate()` consumes one complete `int16_t audio[4096][7]` window at 48 kHz. Channels are D0L, D0R, D1L, D1R, D2L, D2R, D3R_CENTER. The caller must discard windows with dropped samples or stalled capture. The function checks clipping itself.

The reference is the existing HF2 Gap code: 18–22 kHz, 2048 active samples followed by 2048 silent samples. This implementation cannot accept arbitrary imported beacon files. The phone audio and sample rate have not changed.

`valid` means the current window has a supported arrival fit. It does not include the two-code-hit temporal confirmation. The caller counts `code_channels >= 4` detections with actual sample timestamps less than 750 ms apart; capture faults and clipping reset that evidence. A geometric rejection is distinct from absence of the code. There is no previous-angle veto or held output.

The angle is the raw array bearing: 0 degrees toward U7/M0, increasing clockwise. Geometry is frozen to the current 40 mm radius and 343 m/s sound speed. Physical channel orientation remains to be verified. Desktop Set Front / mirror settings are not applied. `arrival_samples` contains the selected, retained peak positions relative to the frame's common envelope center; missing peaks are NAN.

## Algorithm and differences from the desktop path

1. Check original PCM clipping, remove each channel's mean and compute a 4096-point float FFT.
2. Match positive bins 1536–1877 against the fixed reference. Apply the existing bounded partial whitening: exponent 0.65, magnitude floor 0.12 times its median, gain clipped to 0.025–3. This is numerical weighting, not microphone gain.
3. Inverse FFT gives an analytic matched-filter envelope. Detect a channel when peak-to-background ratio is at least 12.5 dB and original band RMS is at least 0.25 in int16 units. Noise excludes a circular 24-sample radius around the maximum. Gap concentration remains diagnostic and is not a gate.
4. Accumulate normalized envelopes to locate the common peak. Keep local maxima at least 0.45 of each channel maximum, with log-parabolic sub-sample interpolation. At most 96 peaks per channel are stored; overflow produces an explicit invalid result rather than silently selecting peaks.
5. Match the existing arrival fallback eligibility: at least six code-positive channels before fitting, at least five retained channels afterwards. Consider peak clusters within ±96 samples of the common arrival; fit `-arrival = position * Fs/c dot direction + intercept`. The negative sign is essential to avoid reversing direction.
6. Use weighted least squares, optionally excluding one outlying microphone, with the existing residual, projection, strength and quality thresholds. Prefer the earliest supported arrival cluster, never a previous angle.

This first port omits the desktop primary spectral-delay solver and joint spectral rescue. It also omits display smoothing and temporal confirmation. Compare it against the desktop arrival-only path when testing numerical fidelity; compare against the full desktop path separately when assessing behavior changes.

An initial native fixture sweep found a different random code with the same band and gap timing that passes the existing 12.5 dB detector on all seven channels. The Python arrival path accepts the same fixture. This is an existing code-selectivity limitation, not a C numerical mismatch; keep that rejection test as a visible failure. No threshold or phone waveform has been changed to hide it. A geometric direction fit does not authenticate the intended beacon.

## Files and resource limits

| File | Role |
|---|---|
| `gap_dsp.h` | Public API and reason codes |
| `gap_dsp.c` | Portable C99 FFT, matched detector and arrival fit |
| `gap_tables.h` | Generated float reference spectrum and quarter-sine FFT constants |
| `gap_integer_fft.h` | Optional bounded 32-bit integer FFT butterfly kernel |
| `gap_integer_tables.h` | Generated Q15 quarter-sine values, including exact +32768 |
| `gap_fast_float.h` | Optional binary32 scaling/rounding helpers with libm fallbacks |
| `generate_tables.py` | Deterministic NumPy generator for both backends, verifies the original PCM template hash |

Only `gap_dsp.c` is compiled; link the math library. There is no heap allocation, SDK, serial, clock or operating-system dependency. The estimator is not reentrant: one caller owns the shared workspace.

The static workspace has a compile-time limit of 56 KiB and is reported by `gap_workspace_bytes()`. It includes the optional profiling state and clock pointer: 55,944 bytes on a 32-bit target, 55,948 with an 8-byte native pointer. It excludes the caller's 57,344-byte PCM window, stack and code/constants. The constant tables occupy 6,836 bytes before linker alignment. FFT workspace is reused across all seven channels; full seven-channel envelope arrays are not retained. Float math cost on RP2040 must be measured rather than inferred from desktop timings.

## Selectable FFT backend

The default build uses `GAP_INTEGER_FFT=0`, preserving the float baseline. `GAP_INTEGER_FFT=1` enables the integer candidate; select it explicitly in CMake or a native compile. `gap_fft_backend_name()` identifies the linked choice. Do not describe a candidate as deployed merely because its native tests compile.

The integer branch normalizes each transform using a shared power-of-two exponent, converts coordinates to bounded int32, divides every radix-2 stage by two, and restores the original forward/unscaled or inverse/4096 amplitude at the boundary. Twiddles use Q15 with +32768 stored in int32. High/low word multiplication avoids a 64-bit multiply; negative divisions implement mathematical floor explicitly. Float and integer arrays share the same 32 KiB union; each element is copied to a local value before its representation is overwritten.

`GAP_INTEGER_FAST=1` is a separate optional optimization for the integer branch; its default is also 0. Normal binary32 power-of-two scaling and half-away rounding use exponent/mantissa operations. Signed zero is preserved; subnormal, nonfinite and scaling-boundary cases retain the original library calls. Integer-to-float rounding still occurs before restored exponent adjustment. The FFT input normalizer guarantees the float-to-int result is representable; arbitrary NaN/Inf/out-of-int32 inputs are not a supported integer-conversion API. Compile-time checks require binary32 precision/range and sign-propagating right shift. The fast integer butterfly uses that checked shift for exact floor division, with the original portable formulas retained under flag 0. This option must pass bit-level helper and full-frame equivalence tests before board measurement; it does not relax freshness.

The fast-option oracle passed on 12 November: all 580 complete 84-byte result structures match the previous integer backend byte for byte. Preparation and restoration each matched 66,519,040 values across 8,120 transforms. Independent checks covered 117,984 defined-domain round conversions, 214,778 power-of-two scalings, 60,216 Q15 multiplies and 20,027 floor halves, with zero differences. Invalid float-to-int reference casts were excluded rather than invoking undefined behavior; the production normalizer's bounded domain was covered. Evidence: `integer-fft/fast-oracle/fast-oracle-results.json` in the dated local output. This establishes numerical equivalence to the earlier integer candidate, not a measured board speed or a cure for wrong-code acceptance.

## Optional whitening stage optimizations

Two independent flags default to 0 so the previous fast-integer implementation remains available:

- `GAP_MAG_CACHE=1` stores the first band-magnitude calculation in unused FFT real slots 0–341, avoiding a second square root for each of 342 bins on each of seven channels. The target band 1536–1877 is disjoint. All non-target bins are cleared after consuming the cache, before inverse FFT. No additional workspace is allocated. This path is intended to preserve computed values exactly and must be checked independently.
- `GAP_WHITEN_FLOAT=1` evaluates the same positive-ratio power as `expf(0.65f * logf(ratio))`, with the original 0.025–3 gain clamps. The SDK's generic `powf` uses double-precision logarithm/exponential intermediates for this exponent. The float form is a numerical approximation, so it requires a separate 580-window comparison and weak-edge checks; it must not be described as bit-identical without evidence.

Neither flag changes the signal band, code, PNR 12.5 dB, geometry, angular-motion policy or result expiry. Measure background and code-present windows separately: accepted code adds envelope normalization, peak processing and potentially arrival fitting. A shorter background time alone does not establish the latency of a usable bearing.

Only FFT arithmetic changes. Whitening, matched reference, PNR 12.5 dB, RMS, geometry, arrival-fit criteria and unrestricted frame-to-frame angles remain identical. Quantization can still affect threshold-near decisions, so the same synthetic, recorded, background, wrong-code and weak-signal fixtures must be compared against float before board acceptance. The wrong-code limitation above is not solved by changing the FFT backend. Each backend needs its own measured board time and source/artifact hashes.

Native comparison on 12 November covered 580 windows, including 144 full-circle synthetic cases, 40 recorded windows, 160 background windows, 128 wrong codes plus a known control, 64 weak-edge cases and rejection/repetition/large-turn cases. Integer and float had no `valid`, reason or detected-channel-count differences. The largest common-valid bearing difference was 0.036026 degrees and the largest per-channel PNR difference was 0.002485 dB. These measure numerical agreement, not physical angular accuracy. Both backends retain three false acceptances among the 128 additional wrong codes and 19 valid windows among the 64 weak-edge cases. The numerical-equivalence check passes; unrestricted production acceptance does not. Machine-readable evidence is `integer-fft/integer-dsp/integer-vs-float.json` in the dated local validation output.

## Optional phase timing

`gap_set_clock_us()` accepts a caller-supplied `uint32_t` microsecond clock, or NULL to disable timing. `gap_get_profile()` returns the most recent `gap_profile_t`; copy it before resetting the estimator. `gap_reset()` clears the counters but retains the configured clock. Each estimate resets its counters, and unsigned differences tolerate a clock wrap within a phase.

The forward/inverse FFT fields time the FFT calls; in the integer backend this includes normalization, conversion and amplitude restoration around the integer kernel. Whitening includes band RMS, the magnitude median and weighted template multiplication. Envelope/peaks includes envelope magnitude, PNR and peak extraction. Arrival-fit includes the common-center search, cluster selection and geometry solution. Totals accumulate seven channels; input validation/loading and the caller's confirmation/UART work remain outside these fields. Timing is observational and does not change signal arithmetic or thresholds.

Reference PCM16LE SHA-256: `87731c4edad62174a04c507f843c1a331785f9b8289517f7162d161cee85eadd`. The generator refuses to write tables if the reproduced waveform differs from that hash.
