# HF1 change details

**Stage 1 · 2026-10-22 · Host-side 16–18 kHz reception and phone-test handoff**

## Signal and receiver

`beacon_dsp.py` adds `coded-16-18` (16,000–18,000 Hz, 17,000 Hz nominal center). Its 4,096-sample known code repeats at 48 kHz. Twenty-four iterative clipping/spectral-projection steps select a lower-crest waveform while retaining the target spectrum. The exported waveform is not clipped. Peak amplitude is 0.35 full scale, versus 0.12 for the retained older beacons. This changes the emitted digital signal, not the sensor's analog gain. Old audible and 20–22 kHz templates remain unchanged.

`highband_dsp.py` is used only by this profile:

1. Validate shape, finite samples, packet health and clipping; clear temporal evidence on faults.
2. FFT the synchronous channels; calculate raw band RMS/dBFS before weighting.
3. Apply partial spectral whitening with exponent 0.65, bounded to 0.025–3.0, to reduce a dominant narrow spectral line and response tilt. Nulls are bounded rather than amplified without limit.
4. Match the known code. Require PNR ≥12.5 dB, peak-energy concentration ≥0.12, band RMS ≥0.25 PCM16 units and at least four channels. The old thresholds were 14.5 dB and 0.18. A plain frequency match cannot authorize a bearing.
5. Isolate the common code-arrival region (±96 samples) and combine two strong-signal or up to three weaker-signal bursts within 0.75 s.
6. Search bounded complex coherence across frequency for each microphone-pair delay, allowing a free carrier-phase intercept. The 17 kHz carrier phase alone cannot choose a direction. Reject poor coherence, narrow frequency support and flat delay curves.
7. Fit array geometry with robust weighting. At most 20% of pairs may be trimmed when at least ten are available. Report both all-pair and retained-pair residuals. Gates include retained RMS ≤1 sample, all-pair RMS ≤1.5 samples, horizontal projection 0.25–1.3 and quality ≥0.48.
8. Require two consistent bearings, then smooth with the existing geometry/front/mirror settings. Rejecting a direction clears the arrow; this is not a promise of continuous tracking.

This is digital processing. It cannot restore high-frequency acoustic energy that never reaches the microphones or claim increased analog microphone sensitivity.

## Interface and measurements

- `app_controls.py`: replaces playback/acquisition controls with `ScanControls`; no audio output backend.
- `sen0325_simple_view.py`: three main buttons (**Start Scan**, **Set Front**, **Advanced**); receiver selection, real band level and five tone-level probes. Phone Audio Files is inside Advanced. Existing calibration, reconnect, charts and trial recording remain.
- `sen0325_launcher.py`: explicit profile-to-center-frequency mapping, `--profile` selection, probe values in logged estimates, unchanged USB packet validation. Discard results from an older capture generation after stopping/switching.
- `Start-16-18kHz.cmd`: launch directly into this receiver with acquisition off. The existing Start-Localizer entry still defaults to the audible receiver; both use the same receive-only interface.
- `probe_levels`: median channel RMS, ±150 Hz around 1/16/17/17.5/18 kHz, dBFS. Reuses the high-band FFT. The audible path uses an additional FFT for these diagnostic values. No display gain or sound-pressure calibration is applied.
- `Record 10 s` includes the profile, manually entered distance, code hits, accepted directions, frequency levels and underlying log path. It does not record the phone volume, actual file or true angle automatically; write these on the test sheet.

## Phone assets and reproducibility

`audio/phone/HF1-MP3/` contains two 12.288 s coded files and five 20 s pure tones. Pure tones share −20 dBFS active-channel RMS and 30 ms fades. All assets have a silent left channel and an active right channel; the phone/player determines actual speaker routing.

Encoding: FFmpeg/libmp3lame, 48 kHz, 320 kbps CBR, compression quality 0, lowpass cutoff 22 kHz, joint stereo disabled. The explicit cutoff avoids relying on encoder-selected bandwidth. See the [official FFmpeg codec options](https://ffmpeg.org/ffmpeg-codecs.html#libmp3lame). `tests/generate_phone_mp3.py` creates the files and checks actual decoded spectra, level, clipping, channel routing and known-code compatibility. It uses the optional generation dependency `imageio-ffmpeg==0.6.0`; the receiver runtime still only needs the original requirements.

`mp3-validation.json` records filenames, hashes and decoder results. It tests files and artificial plane-wave delays after decoding, not a phone speaker or room. The 16–18 kHz decoded in-band energy fraction is 0.999985; each coded asset matched all 16 sampled windows. Pure tones were not accepted as directions.

## Evidence and limits

- `model-validation.json`: 30 positive generated cases, 84 three-window negative groups, corruption/clipping guards, legacy audible regression and an old/new receiver sensitivity comparison. Maximum accepted generated-case error 13.502°, not a hardware angular specification. Median processing 13.01 ms / maximum 32.92 ms in this run; host load affects these figures.
- Receiver-only comparison uses the same 16–18 kHz template and samples for both algorithms. In the colored-response/noise case at source RMS 18, code-hit windows changed from 0/18 to 15/18. With an added narrow tone at source RMS 25, they changed from 0/18 to 18/18. The weaker RMS 8 and 12 cases remained 0/18. These are generated PCM amplitudes, not meters.
- `pico-ui-validation.json`: 36 real bursts, seven channels, three buttons, 15 checks, no callback errors. Observed steady capture/detection-loop rate 4.27 Hz; display refresh 21.28 Hz. No phone source was played. Startup and USB warmup are not represented by the steady rate.
- `pico-capture-summary.json` and the copied raw launcher log preserve ambient-capture evidence.
- `controls-validation.json` and `english-ui-validation.json` cover scan state, late-burst rejection, English labels and layout. Offline UI checks make no hardware claim.

Pico `main.c`, the supplied RAM UF2, `runtime_tuning.py` and existing `array_geometry.json` are unchanged. No new GPIO wiring, firmware flash, ESP32 link or motor control is included. The 17 October weekly ZIP remains frozen. The pre-stage host snapshot is `before-stage-1.zip`; close the app before manually restoring from it. Use the old audible entry after a rollback because the old launcher does not support the new profile.

## Next acceptance gate

Use the test sheet to distinguish background-limited reception, missing code and inconsistent direction. Do not start general latency/range tuning until the phone comparison is reviewed. Reliable >1 m operation and inaudibility remain open measurements.
