# Tale of Immortal Android — v0.3.8.1 Experimental Item Binding Repair

Date: 7 November 2026. Branch: build/toi-v0381-nested-bindings-20261107. Baseline: LiteAPK v0.3.6 source + private v0.3.7 Item Manager + private v0.3.8 NPC/Sect overlay. Keep separate from V60.

## Confirmed original Android symptoms
- Standard item: at least one item — APPLIED (single screenshot; not all items proven).
- Manual: BLOCKED, Checked native manual generator unavailable.
- Devil Demon: BLOCKED, Native item reward method unavailable.
- Artifact: BLOCKED, Checked native Artifact factory unavailable.
- NPC list: 2149 total in user's tested save, 20/page, read-only confirmed.
- NPC stat/grade and Sect EXP effects: coded but not proven on Android.
- Sect breakthrough materials, AI scheduling, manual-quality improvements: not implemented.

## Root-cause evidence and scope
The original supplied metadata SHA-256 is 9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3 (identical across tales.zip and file 3.zip). Old source checked short type names that disagree with IL2CPP nested types:
DataProps.PropsData, DataProps.PropsArtifact, WorldUnitData.RewardItemData.
The original libil2cpp.so exports il2cpp_class_get_nested_types, il2cpp_class_from_name and il2cpp_type_get_name.

Changes:
- Added checked nested class iterator to ManagedApi, loaded from actual IL2CPP export.
- Narrow ManagedAccess::klass nested lookup to DataProps.PropsData and DataProps.PropsArtifact only.
- Corrected nested method return/parameter type names and Artifact data field expected type.
- Separated generic Manual/Artifact BLOCKED messages into named missing binding/token diagnostics.
- Kept token/signature checks, item policy, validation and readback unchanged.
- Did not touch Java UI, NPC stat/grade, Sect policy, item IDs, quantities or gameplay save.

Patch source: https://github.com/hanzirei-ux/Tale-of-immortal-/blob/build/toi-v0381-nested-bindings-20261107/development/liteapk-v0.3.8/patches/apply_v0381_nested_bindings.py
Mock test: https://github.com/hanzirei-ux/Tale-of-immortal-/blob/build/toi-v0381-nested-bindings-20261107/development/liteapk-v0.3.8/tests/test_nested_bindings.cpp

## Build and tests
GitHub Actions run #42391732939 — SUCCESS:
https://github.com/hanzirei-ux/Tale-of-immortal-/actions/runs/42391732939

Successful steps: private source ZIP hash, restore overlays, guarded patch, C++ syntax, host mock exact nested lookup/strict signatures and wrong-token rejection, original NPC scope policy test, Android SDK/NDK ARM64 compilation, DEX build, artifact SHA verification and upload.

Artifact: TOI_ItemBindings_v0381_ANDROID_TEST_PATCH
https://github.com/hanzirei-ux/Tale-of-immortal-/actions/runs/42391732939/artifacts/13581478650
Expires 2026-11-14; not a complete APK.

Inner package: TOI_ItemBindings_v0.3.8.1_ANDROID_TEST_PATCH.zip
- classes2.dex — 765,688 bytes; SHA-256 f6b63b4da6554051d3065f43e18f7411686e0d768b8576f3c3b38e4bf737a927 (same exact hash as v0.3.8).
- lib/arm64-v8a/libtoimodmenu.so — 835,136 bytes; SHA-256 e51294cdc0cf4f6b8e6b275e6c374b08a50e878ce7d8fa59327c1cac53375977 (changed native binary).
- build_manifest.json includes patch_revision 0.3.8.1-nested-il2cpp-item-bindings and runtime_item_add_verified=false.
- Internal source baseline version remains 0.3.8; do not confuse this experimental revision with a stable release.

## Device test, step-by-step, disposable save only
1. Back up actual save data and currently installed APK; preserve original matched v0.3.8 DEX and SO.
2. In the confirmed matching v0.3.8 integration, only ARM64 SO needs replacement; DEX is byte-identical. Do not mix with old V60/custom binaries.
3. Confirm game launches, old menu/hook status, and one previously working normal Add Item; inspect bag.
4. Test ONE Manual with Realm/quality in a copied save. Capture Last result > Details and inspect bag. Never repeat an INVOKED_UNVERIFIED result without inspection.
5. If safe, test ONE Devil Demon with Gourd open; inspect Gourd bag. Then ONE Artifact and inspect Realm/quality and save/reload.
6. Check old currency, catalog and NPC list functionality. Do not test NPC Realm upgrade or high-risk heroine editing in this batch.
7. On freeze, force-close, invalid item, ambiguous receipt, or save corruption, STOP and restore matching old SO/DEX + backup save.

## Outstanding
No direct Android runtime evidence yet that Manual, Demon or Artifact creation works. Fixed binding may expose secondary missing signatures/constructors or gameplay conditions. NPC name/nearby search is not implemented. NPC stat/grade mutation remains unverified. Sect system beyond positive cultivation EXP multiplier remains unimplemented.

STATUS: Host tests / Android build / package integrity VERIFIED; gameplay fix PENDING DEVICE TEST.
Only this isolated build branch was modified. Stable main and original v0.3.8 branch remain unchanged.
