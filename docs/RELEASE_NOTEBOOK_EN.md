# Release-stage engineering notebook
## Request and boundaries
Prepare a complete teammate/AI handoff of the current microphone → Pico → ESP32 milestone; English software, separate English/Chinese explanatory documents, concrete platform details, a clean local tree and matching GitHub update. Keep only the final Pico + computer template in legacy. Do not optimize FFT or change motor behavior in this documentation/communication stage.

## Decisions and reasons
Use separate Pico SDK and Arduino folders because their toolchains, build options and responsibilities differ. Preserve source and deployed-image hashes so a successful compile is not confused with installation. Keep invalid finite fits visible for diagnosis without changing valid/expiry. Preserve measured packet equality separately from unknown physical angle error. Put discarded history outside the active tree, with hashes, to keep engineering assets recoverable.

Use an isolated Git checkout because the local project inherits a parent EE475 repository. Generate a shareable-file allowlist; exclude logs, device backups and signing materials. Update local files before publishing, then verify per-file parity. Use PowerShell/Git rather than browser manipulation.

## Completed changes
The active firmware/source and phone reference remain fixed for this stage. The viewer setup no longer points into the removed root combo folder. Start.cmd and Update.cmd are the two main entries. README explains the Arduino package vs NodeMCU board vs COM port distinction, and Pico SDK/compiler/flash usage. Components, GPIO, data rates, pseudocode, predicted bugs, test evidence and limitations have separate bilingual guides. The final combo source/binaries are unchanged while its documentation and ZIP are refreshed.

## Acceptance
Local catalog/checksums and links must pass; portable protocol/monitor checks must pass; known DSP negative failures must remain visible; template source/binary identity must pass; release diff must exclude private data; local shareable files must match the final Git commit. Physical acoustic accuracy, fresh control targets, cold power-cycle and the delay goal are not release claims.

## Evidence
See reports/communication-2026-11-12/REPORT_EN.md, pico-standalone/COMMUNICATION_NOTEBOOK_EN.md and the final template validation. Exact local migration/board backup records are private. These notes summarize engineering decisions and verifiable evidence, not a transcript of internal reasoning.
