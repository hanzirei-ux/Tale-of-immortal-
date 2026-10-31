# Tale of Immortal Android Mod Menu v0.3.1

Stability hotfix continuing the compiled v0.3.0 and working v0.2 integration. **COMPILED — NOT DEVICE TESTED.** No NPC editor or new gameplay expansion.

This fixes recoverable missing localization keys, ambiguous/stale control failures and checkbox recursion, preserves a valid player combat binding across data refreshes, and makes the high-contrast Android menu compact. Per-hook/per-control diagnostics report policy acceptance separately from gameplay verification. The seven currency/resource editors and persistent inventory capacity implementation are retained.

See [PATCH_REPORT.md](PATCH_REPORT.md), [CHANGELOG.txt](CHANGELOG.txt), [README_ID.txt](README_ID.txt), [TEST_CHECKLIST.txt](TEST_CHECKLIST.txt), and [BUILD_V031.md](BUILD_V031.md). Install the matching DEX and SO together; protocol 4 intentionally rejects an older pair. Preserve the installed v0.2 primary DEX and original game files.

The source and compiled helper patch contain no original game APK, IL2CPP/metadata/assets or private saves. Archived v0.3 files elsewhere in the repository remain the rollback reference. V60 is a different historical custom build.
