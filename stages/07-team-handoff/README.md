# Stage 07 — Team handoff and GitHub packaging

Date: 2 November 2026. Receiver remains RX4; firmware remains v0.6-RX2. This is a delivery stage, not a new direction estimator or waveform experiment.

See ../../docs/TEAM_HANDOFF.md and ../../docs/TEAM_HANDOFF_ZH.md. Changes: English/Chinese team handoff, AI continuation instructions, architecture/interface boundaries, per-file catalog, setup guide, Android delivery notes, and an explicit repository/local-only separation.

Small portability changes: launcher can use a project .venv or EE475_PYTHON; picotool can be selected with EE475_PICOTOOL; source validation creates its logs directory on a fresh clone; CMake accepts PICO_SDK_PATH; Android build reads configurable Python/keystore paths; one UI test's output location was corrected. Existing local tool paths remain the fallback. No DSP threshold, waveform, angle-jump policy, GPIO or current firmware binary was changed.

The complete pre-handoff local backup was verified as a ZIP. File hashes, offline results and release hashes are generated alongside the delivery. A clean source export is checked without private captures. Full historical replay still needs the owner's original recordings. Phone and physical angle acceptance remain outstanding.
