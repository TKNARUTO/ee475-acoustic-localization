# Roles and responsibilities

The EE475 contribution in this repository covers SEN0325 + Pico audio capture, desktop beacon reception, bearing visualization, validation and a local phone transmitter app. The phone emits sound; SEN0325 receives; Pico supplies synchronous digital capture; the PC estimates direction. Radar rings are not measured range.

The human operator owns physical wiring, power checks, phone playback/volume/pose, interruption notes and ground-truth measurements. The coding agent maintains code, bounded tests, reproducible evidence and documentation, and explains behavior changes before applying them. Large angular changes must not be suppressed solely because of their size.

ESP32 motor control, the front distance sensor, obstacle handling and autonomous vehicle following are separate integration work. No current module commands a motor. Teammate assignments and person names are not invented here.

`SEN0325-Pico-Setup` is active code; `tests` validates it; `audio` contains transmitter/reference inputs; `stages` freezes checkpoints; `reports` explains findings; `references` preserves source documents; `legacy` preserves superseded material. Current tests may read legacy fixtures but must write new evidence into the current checkpoint.
