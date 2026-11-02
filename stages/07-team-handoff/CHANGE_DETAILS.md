# Stage 07 change details

2 November 2026. Packaging and portability only; RX4 algorithms and current firmware are unchanged.

| Change | Reason | Verification |
|---|---|---|
| Team/AI handoff, interfaces, file catalog | Let another person or agent find the current source and understand what remains unfinished | New current documentation links checked; Git-selected catalog generated |
| Project-local Python setup and configurable picotool | Remove dependency on one owner workstation for desktop use | Clean export imports and offline checks passed; fresh dependency installation remains untested |
| Create logs directory during source check | A clone intentionally does not include runtime logs | Clean export check passed without a pre-existing log directory |
| CMake SDK path override | Permit an externally configured SDK | Source change only; current firmware binary retained and hash-checked |
| Configurable Android Python and keystore | Let teammates build with their own local paths without sharing a key | Build completed; APK v2/v3 signature and alignment passed; nine gain checks passed |
| Explicit output option for protocol/joint tests | Save this stage's results without overwriting old evidence | New results saved under stage 07 |
| Separate team ZIP and full local ZIP | Keep original recordings and machine state local while sharing useful project material | ZIP CRC, per-file hashes and selected-content scan passed |

Private baseline captures were used locally for the full RX4 replay. A fresh shared export separately passed six offline check groups without those captures. No new physical acoustic, phone or range acceptance is claimed. No angle-jump veto was introduced.
