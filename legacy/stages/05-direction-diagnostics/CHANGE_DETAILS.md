# RX3 change details

## Code confirmation

Previously, high-band bearing confirmation was counted only after a geometric fit passed. A failed fit cleared the count. The following fit also had to remain within 20° of the previous candidate, so legitimate turns and isolated fit failures could restart the wait.

`highband_dsp.confirm_code` now advances on consecutive code-matched windows, before geometric fitting, with the existing 0.75 s freshness bound and two-window repeat requirement. A failed fit remains invalid but preserves current code evidence. Silence/no-code, clipping, malformed data and capture-health faults clear confirmation. Candidates and their angle changes remain diagnostic observations; they do not gate output. Smoothing is unchanged. Session capture-generation changes recreate the estimator, preventing Stop/Start or mode transitions from reusing confirmation across acquisition contexts.

The original 27 October frozen event log contained 126 waiting-for-confirmation windows; 121 already had repeated code presence. That is a state-only replay finding, not raw-audio re-estimation. Two newly captured raw snapshots separately verify the output difference on identical audio.

## Diagnostic fields

`highband_dsp.py` emits per-channel code presence, PNR, concentration, unamplified band level and interpolated matched-filter peak. Per-pair diagnostics include delay, coherence, effective spectral support, score spread, fit retention and residual. `arrival_dsp.py` adds peak counts, cluster rejection reasons and retained-channel residuals. The delay search, pair selection, arrival acceptance, thresholds and fitting calculations are numerically unchanged. Synthetic A/B checks compare the same fit candidates and residuals with RX2.

## Automatic raw capture

`direction_diagnostics.py` buffers short, independent local snapshots. It triggers on six successive code-hit delay failures or four successive valid bearings, with eight pre-blocks, twelve post-blocks, a 15 s cooldown and two snapshots per type per app session. The serial worker copies blocks and submits bounded jobs; another thread writes uncompressed NPZ plus JSON. A full writer queue skips optional evidence; write errors are reported without failing acquisition. Context changes split pending snapshots; normal worker shutdown flushes partial evidence.

Metadata includes sequence, received timestamp, generation, capture health, full estimates, current geometry and SHA256 of the NPZ. Geometry and phone playback state are not inferred. Metadata `valid_reference` means algorithm-accepted output, not a known-angle reference.

## Replay and experiments

From the project folder, using the configured Python runtime:

```powershell
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\tests\verify_direction_diagnostics.py'
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\tests\verify_highband_20k.py' --output '.\stages\05-direction-diagnostics\model-validation.json'
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\tests\verify_controls.py' --output '.\stages\05-direction-diagnostics\controls-validation.json'
& 'C:\Tools\Embedded\venv\Scripts\python.exe' '.\tests\replay_direction_diagnostics.py' '<absolute snapshot JSON path>'
```

Replay verifies raw checksum, shape and sequence, and creates fresh RX2/RX3 estimators over identical blocks. Both warm up at snapshot boundaries. `explore_direction_capture.py` tests single-burst input offline; `analyze_delay_closure.py` checks arbitrary-arrival-time and triangle consistency. Neither changes active software.

## Preservation and rollback

Pico ELF/UF2 bytes and `array_geometry.json` match the baseline hashes. GPIO wiring, sample order, beacon file, band limits, gain, transport/CRC, geometry thresholds, smoothing and the four main UI buttons are preserved. Historical RX1/RX2 and phone-observation reports are retained. Test scripts now accept an explicit output path so this stage does not overwrite earlier benchmark evidence.

To roll back, close the app, restore `highband_dsp.py`, `arrival_dsp.py` and `sen0325_launcher.py` from `backups/before-RX3.zip` into the active workspace, then reopen Start-20kHz. Keep the new evidence and recordings. The standalone diagnostics module can remain unused; no firmware rollback is required.
