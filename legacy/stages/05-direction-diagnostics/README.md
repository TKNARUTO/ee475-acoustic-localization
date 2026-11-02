# RX3 — Direction continuity and per-channel delay diagnosis

EE475 / 27 October 2026 / desktop RX3 / unchanged Pico firmware **v0.6-RX2**

RX3 fixes repeated waiting after an already detected beacon. Code presence is confirmed separately from bearing validity. A rejected geometric fit no longer clears confirmed code; the next valid fit can immediately produce a bearing. Large turns do not reset confirmation. All existing geometric acceptance thresholds stay in force.

## Run and test

1. Open `EE475/Start-20kHz.cmd` and select **Start Scan**.
2. Loop the existing `audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3` on the phone. Computer playback remains disabled.
3. For a short comparison, keep phone position and orientation fixed for approximately 30 s. Note the physical side, approximate distance and any pause. Then move it slowly to test tracking separately.
4. Direction and signal plots keep their existing controls. No new button is required for automatic diagnostic snapshots.

After six consecutive code-hit delay failures, or four consecutive valid bearings, the app saves a short raw snapshot under `SEN0325-Pico-Setup/logs/direction-diagnostics/`. Each capture contains up to eight preceding blocks and twelve following blocks (about 3.8 s at the observed update rate). There is a 15 s trigger cooldown, a maximum of two captures of each kind, and at most four captures per app session. Raw PCM storage is at most about 4.6 MB per session, plus JSON metadata; ordinary launcher text logs are separate. Saves run on a background writer. Scan/mode changes and capture gaps split snapshots instead of mixing contexts. Closing the app flushes a partial snapshot.

The snapshots are local seven-channel microphone recordings. A new app session resets the capture budget. Existing Advanced → Record 10 s remains available for manually labelled trials.

## Evidence

- 20 targeted confirmation/diagnostic checks passed, including unrestricted synthetic turns, rejection of inconsistent delays, raw sample/sequence preservation, bounded storage, context separation, write-error isolation and checksum-verified replay.
- Existing 20 kHz model regression passed: generated angles, colored/noisy signals, narrow interference, carrier phase offsets, echoes and negative inputs. Maximum accepted synthetic error: 12.967°. This is not a physical precision measurement.
- Actual GUI/Pico smoke check: 21 checks, 87 captured blocks, seven channels, four main buttons, 5.32 Hz detection updates and 31.25 Hz UI refresh.
- Two real phone snapshots, 20 blocks each, were replayed identically through RX2 and RX3: accepted outputs changed **1 → 5** and **0 → 2**. Their geometric rejections stayed **12** and **14**, respectively. Snapshots were selected by failure triggers, so these counts are not an overall success-rate estimate.
- In 25 analyzable rejected windows, 20 still had more than one sample RMS residual when fitting arbitrary per-microphone arrival times. Median residual: 2.2805 samples. Thus some pair-delay estimates disagree before array geometry is applied; this does not identify a faulty microphone.
- An offline single-burst experiment added only one accepted output across the two snapshots. It was not deployed.

## Files and next step

- [Chinese phase notes and findings](PROGRESS_NOTES.md)
- [Implementation and rollback details](CHANGE_DETAILS.md)
- [Chinese continuity report](../../reports/direction-continuity-2026-10-27/DIRECTION_CONTINUITY_ZH.md)
- `confirmation-diagnostics-validation.json`, `model-validation.json`, `controls-validation.json`, `gui-validation.json`: verification results.
- `live-observation.json`: bounded log snapshot statistics and limitations.
- `evidence/`: frozen runtime logs and two raw NPZ/JSON pairs.
- `replays/`: identical-input RX2/RX3 comparisons.
- `pair-closure-analysis.json`: pair-delay consistency analysis.
- `single-burst-experiment.json`: offline averaging experiment; not active software.
- `backups/before-RX3.zip`: pre-change sources, geometry and firmware.
- `before-files.json`, `checkpoint-validation.json`, `checkpoint-files.sha256`: baseline hashes, checks and checkpoint manifest.

Next work should improve mutually consistent pair-delay estimation and validate known physical bearings. RX3 improves output continuity when a fit already passes; it does not resolve all delay-fitting failures or establish angular accuracy. No forced 180° correction, hard motion veto, hardware gain change, new phone file or firmware change was introduced.
