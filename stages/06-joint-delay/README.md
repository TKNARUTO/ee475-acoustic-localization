# RX4 — Joint spectral-delay rescue

Started 27 October; resumed and validated **29 October 2026**. Desktop RX4; unchanged Pico firmware v0.6-RX2.

RX4 retains RX3 code confirmation and its unrestricted turn behavior. Only when the existing estimators fail does it score a shared physical delay field against complete reliable pair curves. It requires at least six represented channels, twelve reliable pairs, a valid physical projection, high spectral coherence and a bounded loss relative to independent pair maxima. Current-frame angular peak separation checks evaluate available evidence; previous bearing and turn size are never inputs to this rescue.

The original pair curves are cached, avoiding a repeated FFT/search. The original successful estimates are preserved. Automatic captures label the checkpoint RX4. A local nonce-scoped restart protocol lets Update-and-Start close the compatible app gracefully, release its port, reopen a fresh process and verify its checkpoint and source hash.

## Evidence

- 15 focused checks; 171 deliberately nonphysical coded-delay fields rejected; cache and large-turn checks passed.
- Original 20 kHz noise/interference/reflection regression and scan controls passed.
- Actual GUI/Pico: all 21 checks passed with four main buttons.
- Two historical failure-triggered snapshots: accepted output 7→9 over 40 identical windows.
- New 90.11 s trial: accepted output 52→81 over 493 identical windows, preserving all earlier accepted raw angles. Several intentional playback interruptions occurred; this is not an overall reception-rate test or known-angle accuracy test.
- Firmware ELF/UF2 and geometry preserve their pre-RX4 hashes.

## Files

- [Chinese phase notes](PROGRESS_NOTES.md), [change details](CHANGE_DETAILS.md), [illustrated analysis](../../reports/RX4-2026-10-29/ANALYSIS_ZH.md).
- `joint-delay-validation.json`, `model-validation.json`, `controls-validation.json`, `gui-validation.json`, `one-click-validation.json`: checks.
- `trials/`: original raw recording, timeline CSV, plots and same-input comparison.
- `backups/`: before-RX4 and selected-source checkpoints.
- `evidence/`: frozen GUI logs and supporting results.
- Unselected waveform/gating/subset prototypes are under `../../legacy/experiments/RX4-prototypes/`.

Earlier stages are under `../../legacy/stages/`. No confidence percentage in the app is a calibrated probability of angular correctness. Remaining peak instability requires controlled physical validation.
