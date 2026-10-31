# LiteAPK Mod Menu v0.3.0 — live progress

Updated: 31 October 2026 (Asia/Jakarta).

## Current status

IN PROGRESS. The user reattached the original v0.3 SourceFix, v0.2 reference and tales.zip after a session filesystem reset. The pinned SourceFix archive was accepted and the continuation overlay applied successfully to that project. Android toolchain restoration and final matching DEX/native builds are underway. No final binary patch is published yet.

This continues v0.2 and the existing v0.3 SourceFix. It does not restore V60 patches or add NPC editors. Do not install this development overlay directly in an APK.

## Preserved implementation

- Player currency transactions: Spirit Stones, personal contribution, City Token, distinct Immortal Store Token.
- Player sect resources: treasury Int64, reputation Int32, faith Int64; personal contribution remains separate.
- READ/SET/ADD/SUBTRACT, overflow/underflow guards, native before/after readback, sect scope confirmation.
- Per-player serialized capacity bonus through the already installed DynInt getter. Effective capacity readback and occupied-item protection, accounting for the existing bag plugin.
- Typed request IDs/receipts so catalog responses cannot replace edit results.
- Localized item cache, bounded indexing, pagination and item confirmation.
- Android contrast, detailed operation/managed exception context and diagnostic copy action.

## Validation in this checkpoint

- Recovered editor code compiles with host g++17, -Wall -Wextra -Wpedantic -Werror.
- 215 host checks passed (amount boundaries, capacity +50/+100/+200 plans, bag-plugin scaling, occupied-slot protection, concurrent receipts, method signature/token rejection, exception context, catalog queries).
- These are host logic tests, not gameplay/device verification.
- SourceFix continuation script applied successfully to the exact original archive SHA-256.
- Final Android binaries still pending rebuild/validation. Previous intermediate native and Java compilations occurred before the reset; those outputs were not delivered.

## Required acceptance

Rebuild classes2.dex and libtoimodmenu.so together, validate API/DEX/ELF, preserve the v0.2 main classes.dex and original libil2cpp.so, package the small binary ZIP, then run the phone checklist. Save/load and gameplay tests are not yet device verified.

Game binaries, original APK contents and private saves must never be committed to this public repository.
