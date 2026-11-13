# Teammate and coding-agent handoff
Read the root README_EN.md first for exact platforms and pins. The active components are deliberately separate:

| Owner / module | Owns | Does not currently own |
|---|---|---|
| Acoustic contributor / Pico | SEN0325 PIO/DMA, fixed HF2 matching, array-angle fit, confirmation/age and UART result | Distance, motor power, full navigation |
| ESP32 integration teammate | Current receive/ACK sketch; future safe use of fresh results | Re-running this Pico FFT or treating diagnostic angles as motor commands |
| Phone player | Selecting a local audio file and looping PCM, optional limited gain | Teaching the Pico a new template or calibrating microphone ADC |
| Optional Windows viewer | Radar and timing telemetry, display front, explicit Pause/Resume | Acoustic computation or automatic firmware replacement |
| Operator | Wiring, USB power, known angle/distance/volume, intended playback pauses | Unrecorded ground truth cannot be reconstructed from logs |
| Coding agent | Small scoped changes, decision notes, tests, README/catalog and synchronization | Changing thresholds, audio or pin ownership without describing the behavior change |

## Current contract
Pico v0.2-link_diag, fixed HF2 18–22 kHz gap, 48 kHz, 4096 samples, integer FFT FAST, whitening/cache options off; core0 only. ESP receiver v1.1, classic NodeMCU-32S / Arduino esp32 core3.3.12. Three-wire UART0↔UART2, 115200 8N1. B packets preserve finite diagnostic angle/quality while valid may remain zero. Follow the [protocol README](../esp32-link/gap_receiver/README_EN.md), not an old DOA example.

The independent Pico viewer does not expose the old PC algorithm's arbitrary beacon import or raw spectrum. Those features belong to the [final combo template](../legacy/pico+computer%20combo%20sensoring%20version/README_EN.md). Do not mix its RAM firmware and launchers with the current Flash release.

## What changed in this stage
- Made transmitted-result metadata correspond to the B packet actually queued; a failed send does not claim a new transmission.
- Preserved finite fits as diagnostics even when stale/unconfirmed, while keeping control validity and expiry unchanged.
- ESP logging reports the actual received packet instead of an older cached target angle.
- Matched B ACKs by session/sequence, excluding hello and duplicate ACKs from roundtrip measurements.
- Preserved raw startup bytes and explicitly isolated opening backlog before formal recording; no mid-test filtering.
- Verified persistent Pico Flash and desktop Arduino sketch deployment; tested reboot and operation without a Pico PC client.
- Split platform documentation, tests, firmware and bilingual reports, retaining only the final combo in legacy.

No microphone wiring, beacon waveform, motor code or angle-jump veto was added. Experimental numeric work remains paused.

## Priority for the next stage
1. Read the [current report](../reports/communication-2026-11-12/REPORT_EN.md) and [decision notebook](../pico-standalone/COMMUNICATION_NOTEBOOK_EN.md).
2. Repeat a warmed-up, known-angle phone trial on the current Flash build. The earlier positive phone trial used RAM with the same source/flags; later Flash checks were background.
3. Measure true acoustic-onset latency and controlled angle error. Packet agreement is not physical angular accuracy.
4. When authorized, optimize computation/scheduling toward 0.2–0.5 s and resolve confirmation spacing; retain age semantics.
5. Address known wrong-code false positives using recorded evidence and negative tests.
6. Then design a measured control-loop budget, coordinate calibration, distance interface, stop behavior and pin ownership.

Before edits: state scope and acceptance criteria. After edits: update English/Chinese notes, relevant README, file catalog and hashes. Update the local tree first, then GitHub through PowerShell/Git CLI, compare the shareable file hashes and remote commit. Never add the parent workspace wholesale. Read AGENTS.md for these persistent constraints.
