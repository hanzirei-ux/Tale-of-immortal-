# v0.3.1 stability hotfix

**COMPILED — NOT DEVICE TESTED.** Continues the compiled v0.3 source and v0.2 player-only hook paths. The original v0.3 directory is preserved as rollback.

- [Source](source), [technical findings/status](source/PATCH_REPORT.md), [Indonesian installation](source/README_ID.txt), [short phone checklist](source/TEST_CHECKLIST.txt).
- Binary: `TaleOfImmortal_ModMenu_v0.3.1_StabilityHotfix_BinaryPatch.zip`, 312,574 bytes.
- SHA-256: `ebb7b51e5815a3c2ff029e4a1dd567ab44452d80f7a6f171f51ef45d50d2b112`.
- Both build records use source revision `1fe1aed4e1cd614e6f13086c8e68755a5bd3ae8e6bab1a9be5aef367ab6ecefd`, protocol 4 / 19 JNI descriptors.

Fixed: recoverable/cached missing translation keys (including item_name1041161 and item_name1041162), specific native control outcomes/ranges/readback, stale-result ownership, guarded checkbox rollback, valid combat-controller lifetime on data refresh, compact high-contrast controls and adaptive item list. Currency and capacity writer functions remain source-identical to v0.3; no NPC features were added.

Validation: baseline/prologues/signatures, current host suites, 32,768 capability-mask combinations, typed localization/error tests, nine Java guard/result-state checks, actual DEX/ELF/JNI and package checksums. Detailed counts/limits are in the report. APPLIED is policy acceptance, not a measured gameplay result. No phone, save/load or long-session stability test is claimed.

Original APKs, game binaries/metadata/assets, old primary game DEX and private saves are excluded. Only original helper components, development source/open-source dependencies, notices and reports are published.
