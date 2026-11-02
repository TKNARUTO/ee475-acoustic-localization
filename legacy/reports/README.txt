CURRENT RX3 DIRECTION CONTINUITY (2026-10-27)

direction-continuity-2026-10-27/DIRECTION_CONTINUITY_ZH.md: code confirmation fix, automatic raw diagnostics, identical-input phone replay and remaining inconsistent pair delays. Checkpoint, source backup and evidence are in ../stages/05-direction-diagnostics/.

PHONE OBSERVATION AFTER RX2 (2026-10-27)

phone-observation-2026-10-27/README.md: receive-only 20 kHz phone test; OBSERVATION_ZH.md explains code-hit direction failures and continuous-output periods. Phone audio paused during the test; whole-session no-code counts are not a receiver failure rate. Frozen log and corrected observation.json are included.

CURRENT RX2 LATENCY REDUCTION (2026-10-27)

latency-reduction-2026-10-27/LATENCY_REDUCTION_ZH.md: measured firmware CRC/USB improvements, normal packet latency, UI regression and remaining physical phone trial. Current evidence is in ../stages/04-latency-reduction/.

CURRENT RX1 FOLLOW-UP (2026-10-27)

delay-followup-2026-10-27/DELAY_FOLLOWUP_ZH.md: measured host packet/GUI timing, live injected-fault recovery, scope and remaining phone trial. Current test JSONs and frozen logs are in ../stages/03-packet-timing/.
delay-diagnosis-2026-10-22/: frozen original diagnosis; retained unchanged.

VALIDATION AND PACKAGING REPORTS

validation/: selected acoustic bench reports and repeatable offline checks. Read ../docs/VALIDATION.md before interpreting their numbers. Physical test reports are historical evidence; the English UI check uses no hardware.
packaging-validation.json: original-document, firmware, waveform, source, launch-path and documentation-link checks.
pre-packaging-manifest.json: source/asset hashes before the English packaging pass; excludes active append-only launcher logs and build caches.
release-files.sha256: hashes of the files included in the weekly release.
release-verification.json: final ZIP checksum and member-integrity result.
