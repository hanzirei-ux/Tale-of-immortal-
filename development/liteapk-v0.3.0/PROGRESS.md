# LiteAPK Mod Menu v0.3.0 — development checkpoint

Updated: 31 October 2026 (Asia/Jakarta).

This continues the existing v0.2 menu and v0.3 SourceFix work. It is separate from the archived V60 patches. NPC editors remain excluded.

## Current delivery status

**BLOCKED: the Work session resumed an older v0.1 filesystem snapshot.** The previously uploaded v0.2/v0.3 archives, reattached tales.zip, downloaded Android toolchain, and intermediate compiled outputs are no longer accessible in the resumed filesystem. Searches of saved files did not recover the three packages. No final v0.3 binary patch has been delivered. Do not install an earlier helper DEX with a new incompatible native library.

The next commits will preserve the original new editor code, targeted integration scripts, static findings, and host tests. They are a continuation overlay for the existing v0.3 SourceFix package, not a replacement game or standalone menu. Android recompilation and device tests remain required.

## Work already performed before the session reset

- Matching LiteAPK libil2cpp.so and metadata hashes verified; baseline was not patched.
- Current native image and metadata dumped successfully with Il2CppDumper 6.7.46.
- Inventory root cause traced: propGridNum base setter is a no-op. beibao adds a runtime delegate; editing its base value cannot persist extra slots.
- New capacity implementation uses a player-specific serialized objData bonus through the already installed DynInt getter hook, actual effective-capacity readback, occupied-item protection, and existing bag UI refresh methods.
- Currency paths separated: player Spirit Stones, personal contribution, City Token, Immortal Store Token, and the player's sect treasury/reputation/faith. Personal contribution is not totalSchoolMoney or sect treasury.
- Per-request receipts prevent item catalog responses replacing edit results.
- Localized item cache, pagination, explicit item confirmation, contrast improvements, and detailed exception context were implemented.
- The updated native editor/runtime component compiled for ARM64; helper Java compiled to DEX. Subsequent JNI receipt API changes still require rebuilding the final matching pair. Intermediate outputs were lost in the session reset.
- No new feature was tested on a phone. Previous v0.2 functionality is user-reported device verified only.

## Needed to resume the final binary build

1. TaleOfImmortal_ModMenu_v0.3.0_SourceFix_BuildReady.zip
2. TaleOfImmortal_LiteAPK_ModMenu_v0.2.0_TestBuild_Patch_Source.zip (compatibility/reference)
3. tales.zip (or matching libil2cpp.so plus global-metadata.dat)

Do not upload these game packages or user saves to this public repository. Only original development code, reports, and tests belong here. Keep the user's working v0.2 APK and save untouched until the matching v0.3 binary patch is available.
