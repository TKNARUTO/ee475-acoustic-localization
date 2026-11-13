# Agent instructions
Read README_EN.md, docs/TEAM_HANDOFF_EN.md and the component README before edits. Chinese equivalents use _ZH. This is a Pico SDK standalone HF2 estimator plus a separate Arduino NodeMCU-32S receiver. PC monitoring is optional; the final PC-DSP template is confined to legacy/pico+computer combo sensoring version.
- Work in stages. Record interpreted requirements, assumptions, implementation decisions, evidence and open issues in a readable engineering notebook; do not present a private reasoning transcript.
- Preserve the current communication milestone. FFT, experimental whitening/cache and dual-core optimization are paused until explicitly resumed. Current deployed flags: INTEGER_FFT=ON, INTEGER_FAST=ON, WHITEN_FLOAT=OFF, MAG_CACHE=OFF, PICO_NO_FLASH=OFF.
- Never block a direction solely because its angle changed greatly. Do not pass stale/invalid diagnostics to a motor controller. No motor commands are implemented.
- PC stays receive-only except explicit acquisition Pause/Resume. Phone handles playback. Do not change beacon/profile on one side silently.
- GP0 TX → ESP16 RX; GP1 RX ← ESP17 TX; common ground. Keep array GP6–GP13. Back up existing Flash before replacing it.
- Keep Pico and ESP sources separate. Arduino board is NodeMCU-32S, package esp32 by Espressif Systems 3.3.12. A COM number is local, not the board type. Pico is SDK C/C++, not an Arduino sketch.
- Distinguish fit, confirmed fresh target, update interval, ACK timing, CPU proxy and measured physical accuracy. All observed control targets in this stage were invalid due to age/confirmation.
- Every change batch updates README_EN/ZH and file catalog. Reports and explanatory documents have separate EN/ZH files; English code/interface.
- Local update and verification come first. Use PowerShell/Git CLI to publish the same allowlisted files, then verify remote commit and local-versus-checkout hashes. Never git-add the parent EE475 workspace.
- Raw microphone recordings, logs, device backups, credentials, keys and machine config stay local. Preserve moved engineering files in an external archive with hashes.
- legacy contains only the final combo template and its matching ZIP. Read its own instructions before editing; source/binaries remain unchanged when updating documentation.
- Use finite serial tests and exclusive ports. Close monitors before upload. Playback pauses and unrecorded movement are not automatically bugs.
- Current report: reports/communication-2026-11-12/REPORT_EN.md. Current stage notebook: pico-standalone/COMMUNICATION_NOTEBOOK_EN.md.
