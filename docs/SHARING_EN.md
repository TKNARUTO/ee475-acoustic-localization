# Local-first publication and provenance
The maintainer updates the local project first, finishes tests and the bilingual documentation, then refreshes the catalog and hashes. Only after those steps is the same allowlisted snapshot copied into an isolated Git checkout and committed/pushed using PowerShell and Git CLI. Remote HEAD and the final checkout are compared to the local selected-file hashes. No browser upload is needed.

The local project is nested below another Git repository. Never run an unscoped git add from the parent EE475 directory. The publication checkout is independent so unrelated engineering files cannot be included accidentally. Remote changes must be checked before a normal fast-forward push; do not force-push.

Included: active source/tests, release firmware, reference phone audio, player APK/source, original supplied project references, bilingual documents/reports, aggregate metrics, the sole final combo template and matching ZIP.
Excluded: original microphone recordings, per-run serial logs/warmup bytes, private imports, signing keys/passwords, machine configuration, SDK/toolchain caches, build trees and original board Flash backups.

The historical files removed from active folders were moved to an external local archive, with source→destination paths and SHA256 checks. 418 moved files were verified during the initial cleanup. That local migration map is intentionally not in this public repository because it contains machine paths. Old documents replaced after that migration also have local pre-edit copies. The original combo ZIP is retained in that external backup; the new combo ZIP changes documentation/manifests while preserving all 52 non-document files byte for byte.

The checksum list excludes itself, includes the generated catalogs, and is checked after all edits. ZIP integrity is compared member-by-member with the template. See the [file catalog](FILE_CATALOG_EN.md), the template's provenance manifest, and the [stage report](../reports/communication-2026-11-12/REPORT_EN.md).

Release commands:
```powershell
python tools/refresh_catalog.py
python tools/verify_release.py
```
These commands do not publish. An authorized maintainer separately reviews the isolated Git diff, commits, pushes and verifies the resulting commit. Generated local logs are not part of file parity.
