# LiteAPK Mod Menu v0.3.0 — progress

**Final milestone: COMPILED — NOT DEVICE TESTED.** The matching helper DEX and ARM64 native library are built and packaged. The complete continued v0.3 project is in [source](source), with [technical report](source/PATCH_REPORT.md), [Indonesian installation instructions](source/README_ID.txt), and [phone checklist](source/TEST_CHECKLIST.txt).

Binary patch: `TaleOfImmortal_ModMenu_v0.3.0_Binary_Patch.zip`, 281,242 bytes, SHA-256 `af2cfe42813187819b39fd3f853a3fb280860cacb76ce221602ad8211fa79985`.

Implemented: effective player inventory capacity READ/SET/ADD/SUBTRACT, seven separate currency/sect resource editors, contrast fixes, localized paginated item catalog, real Alchemy recipe item filter, typed operation receipts, initialization guards and detailed exceptions. Existing player combat/EXP hooks are preserved. NPC editors remain excluded. Forge/Talisman recipe filtering/unlocks and optional unlimited currencies are not implemented.

Validation: 27 current method signatures and four currency IDs checked, 28 baseline native prologues verified, DEX/ELF/16 KiB alignment/dependencies checked, all 17 JNI descriptors match, existing host suites and 215 new editor checks pass, plus three APK replacement tests. Phone installation/gameplay/save-load/stability checks have not been run. No signed APK is claimed.

## Checkpoints — 31 October 2026

1. Reused the supplied v0.3 SourceFix and the working v0.2 integration.
2. Verified baseline and identified the no-op inventory base setter and separate resource paths.
3. A Work filesystem reset lost temporary inputs/toolchain/output; recorded the blocker in GitHub.
4. Preserved editor continuation and 215 host checks in commit d03c550.
5. User reattached all three packages; CRC/SHA-256 matched. Applied the continuation and restored the Android tools.
6. Built the actual new DEX/native pair, completed recipe filtering, stack diagnostics and before/after guards, and validated artifacts.
7. Published the canonical source/report and small binary patch here. Use source/ for further work; overlay/ and scripts/apply_to_sourcefix.py describe the earlier checkpoint and are retained as history.

Original game APKs, libil2cpp/metadata/assets, old primary game DEX and private saves are not included. Original development code and open-source notices are retained. The V60 archive is a separate custom project; its patches were not restored.
