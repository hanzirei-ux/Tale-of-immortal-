# Tale of Immortal Android Mod Menu v0.3.1 stability hotfix

The hotfix produces a newly compiled, matching helper DEX and ARM64 library. **COMPILED — NOT DEVICE TESTED.** It continues GitHub source commit `9603fb1560a8e22c9d7b54b98b6698cd741252e6`; the original v0.3 directory and patch remain unchanged for rollback.

The user reports that v0.2 launched and most tested cheats worked. In v0.3 the game/menu/native library still launched with `hooks=15 | player=loaded`, but localization requests failed, controls displayed ambiguous rejections, and the UI was oversized. Those are device reports for the earlier builds, not verification of this hotfix.

## Findings and targeted repairs

### Missing localization keys

`GameEditors::catalog` previously invoked `ConfLocalText.GetText` and returned immediately on any managed exception. This made one absent translation block the whole indexing request. The index was also advanced before that failed row was committed, allowing retries to silently skip failing rows.

The hotfix classifies the actual managed exception using **all** of its class, namespace, method owner and method name: `System.Collections.Generic.KeyNotFoundException` from `ConfLocalText.GetText`. Only this expected missing-key case is recoverable. Unrelated KeyNotFound, NullReference, signature and other errors still produce an operation-specific failure with full managed context.

Names are looked up in the current game language, English, Chinese and, when necessary, other available game languages. If none exists, the real internal key is retained; the row/preview still carries the real item ID. Results are memoized per key/language, including missing lookups, so repeated entries do not repeatedly throw. Expected misses avoid expensive full stack formatting; diagnostics retain counts and up to 16 example keys. Item indexing commits a row only after a resolved/fallback name; unrelated failures do not corrupt its position.

Regression tests use **`item_name1041161` and `item_name1041162`**. They cover both missing together, continuation, alternate languages, category filters, ID lookup, autocomplete, negative-cache reuse and non-localization exception preservation. Actual game-catalog acceptance still requires the phone checklist.

### Combat rejections: evidence and limits

No source change to the core combat/EXP hook bodies or multiplier policy was found between the supplied v0.2 and v0.3. Their profile and control IDs also match. With all 15 adapters installed, the expected supported capability mask is `4194303` (`0x3fffff`, IDs 0–21). A count of 15 alone does not prove that the required capability is active, a combat target is bound, or gameplay effects are working.

The v0.3 UI had confirmed defects: all false returns shared the text `Rejected or hook unavailable`; a successful apply did not replace that earlier error; and programmatic checkbox rollback could call the apply listener again. Spiritual damage 150 is out of the native 0.1–100 range. Defense 16 is valid. The screenshot's generic message cannot establish whether the valid Defense operation actually failed or merely left an earlier message visible.

The new path is Android input -> typed JNI request -> ID/key/range/readiness/hook/capability validation -> the existing canonical PolicyStore -> native state readback -> the unchanged player hook math on the Unity callback. It reports `INVALID_VALUE`, `OUT_OF_RANGE`, `HOOK_UNAVAILABLE`, `CAPABILITY_DISABLED`, `CONTROL_ID_MISMATCH`, `NATIVE_REJECTED`, `NOT_INITIALIZED`, `PLAYER_NOT_LOADED` or `APPLIED`, including control ID/key, requested value, allowed range, capability state and observed enabled/value.

Successful applies clear old failures. Per-control results remain scoped to their control, and epoch-checked asynchronous receipts cannot overwrite a newer operation. Programmatic checkbox changes run under a tested callback guard. A valid OFF operation can still disable a setting during a scene transition. `APPLIED` means policy acceptance/readback; it is not a claim of a measured gameplay effect.

The Diagnostics page reports each of the 22 controls, required hooks, installation status, capability bit, current native state and last apply result. It also reports all 15 hook stages: pending, verified/installed, prologue mismatch, Dobby failure, missing trampoline or unchanged entry. Hook count is no longer the UI's readiness criterion. No capability bits are forced on and no baseline/prologue check is removed.

### Player combat binding across data refreshes

The v0.3 frame path cleared the cached combat controller on `unitInfo`, `dyn` or `worldData` changes, in addition to player/world identity changes. A valid controller acquired during initialization could therefore be lost on a data refresh, until another binding path re-acquired it. The hotfix retains an owner-validated controller when player/world identity is unchanged, matching the v0.2 lifetime rule. Identity changes still clear it; data changes still increment generation and cancel old persistent requests. Core hook bodies, player-only checks, recursion guards, addresses and multiplier precedence are unchanged.

This is a concrete binding-path repair, not proof that it caused every reported rejection. The exact runtime capability/result must be observed in the new diagnostics on the phone.

### Compact landscape UI

The v0.3 foreground/background colors are retained. Header actions share one compact row. Category selectors are about 34dp, text inputs/buttons about 36dp, and combat controls use 40dp enable/name/value/apply rows. The large slider/input/button blocks are removed; small sliders remain for cooldown and energy cost. Per-control status is inline. A 26dp result footer expands only on request.

Item category/search share a row; the item list adapts to available content height, with compact pagination/quantity/Add actions. Selection survives category page rebuilds and is revalidated by native code before Add. The launcher, lifecycle integration and position persistence remain intact. Android rendering, touch comfort and actual screen fit were not tested on a device here.

## Preserved systems

The Currency & Contribution functions, inventory-capacity functions, safeguards and readback paths are source-identical to v0.3. Spirit Stones, personal contribution, City Token 10041, Immortal Store Token 10051, sect funds, reputation and faith remain separate. No equivalence with Chi You Alliance Battle Contribution is asserted. No new currency system, NPC editor, multiplier or gameplay expansion was added.

The per-player `toimodmenu.v03.capacityBonus`, no-op base-setter workaround, occupied-slot protection, ring/plugin scaling, inventory refresh and normal game save serialization are retained. Capacity is **not device verified**. Persistent requests are still queued on Unity's verified thread, generation checked, never automatically replayed by Load, and not inverted by runtime Reset.

## Artifacts and compatibility

| File | Bytes | SHA-256 |
|---|---:|---|
| classes2.dex | 61,268 | `3047bb58ffe729365604d8142471fdf013e47c537cee48a5508fd4763001e7a3` |
| libtoimodmenu.so | 711,848 | `ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729` |

`TaleOfImmortal_ModMenu_v0.3.1_StabilityHotfix_BinaryPatch.zip`: **312,574 bytes**; SHA-256 **`ebb7b51e5815a3c2ff029e4a1dd567ab44452d80f7a6f171f51ef45d50d2b112`**.

Both build records have compile-source revision **`1fe1aed4e1cd614e6f13086c8e68755a5bd3ae8e6bab1a9be5aef367ab6ecefd`**. The content identity covers native/Java source, CMake/config and build scripts, and is checked by the packager. Protocol **4** / **19 JNI descriptors** must match. Legacy C API ABI 2 remains unchanged. Older v0.2/v0.3 components are rejected by the packager rather than renamed.

Native build: NDK r27c (27.2.12479018), Clang 18, CMake 3.22.1, C++17, arm64-v8a/API 23, static C++ runtime. Java: Java 17, ECJ 3.38.0, Android platform 35, D8/R8 8.7.18, DEX 035/min API 23. ELF LOAD alignment is 16 KiB, with RELRO, non-executable stack and system-only shared dependencies.

Baseline `libil2cpp.so` SHA-256 remains `c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099`; metadata remains `9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3` (version 31). No game files were modified on disk. The working v0.2 primary DEX is retained, including original native registrations. `libandroidoyunclub.so`, Unity libraries and assets are not replaced.

This is a component patch, **not a signed APK**. No APK certificate is included; original LiteAPK signing identity was not available for verification. Repack/sign with the installed app's existing key. Xiaomi 11T Android 14 and Android 11 ARM64 remain phone targets; no v0.3.1 device test was performed.

## Validation actually run

- Uploaded v0.3 patch, v0.2 archive and tales.zip passed CRC/hash checks. The GitHub source came from the recorded v0.3 commit.
- Original v0.3 host suites passed before changes. Current suites passed: 26 core cases/94 assertions, 212 policy assertions, catalog tests, 215 editor checks, 35 Python tests and 10 inherited research tests.
- Hotfix C++ suite: 32,834 checks, of which 32,768 enumerate hook-bit combinations against the original v0.2 capability formula. Remaining checks cover localization fallback/error classification, correct range/readiness reasons, policy readback and unchanged NPC scope. Counts are host logic checks, not thousands of gameplay tests.
- Actual Android-independent Java guard/state class: 9 checks for recursive rollback prevention, guard restoration, per-control result ownership and stale receipt exclusion. Android widgets were compiled, not rendered in these tests.
- Source audit: 16 combat/EXP hook/helper bodies plus profile/policy match v0.2/v0.3; eight currency/capacity helper bodies match v0.3 exactly.
- 28 checked managed method signatures, four currency IDs, required API exports and the no-op setter were reverified against the matching private baseline. All 28 profile prologues match executable mappings.
- Actual new DEX header, SHA-1, Adler32/classes/native declarations and all 19 DEX/native JNI descriptors verified. Retained primary DEX classes/native registrations were checked and no helper duplicate classes found.
- Actual ARM64 ELF, dependencies/alignment/protections, paired build revisions, binary freshness, ZIP CRC and every packaged component hash verified.
- Synthetic local APK replacement tests cover old v0.2/v0.3 pairs, checksum/mismatched-native rejection, preserving unrelated DEX/assets and the actual helper slot. No real APK was installed or signed.

## Status and remaining tests

| Area | Status |
|---|---|
| Localization recovery/cache, detailed control path, compact UI | COMPILED — NOT DEVICE TESTED |
| Per-hook/control diagnostics and binding lifetime fix | COMPILED — NOT DEVICE TESTED |
| Combat/EXP source preservation; currency/capacity preservation | STATIC VERIFIED |
| JNI/DEX/ELF/source-revision/package checks | STATIC VERIFIED |
| Phone initialization/gameplay, screen fit, save/load and stability | NOT DEVICE TESTED |
| Signed installable APK; NPC editors; unrelated new features | NOT IMPLEMENTED / outside this hotfix |

Use the short [TEST_CHECKLIST.txt](TEST_CHECKLIST.txt): All Types/Pills/Equipment/Manuals, no blocking KeyNotFound, autocomplete/select/Add; God Mode, damage x2, Defense x2/x16, Spiritual 150 rejection then x2 acceptance, EXP and unchanged NPCs; compact UI/launcher; capacity +50, Spirit Stones +100, save/load and no Force Close. If a control still fails, copy Diagnostics with its exact ID, range, capability, hook stages and native result. Runtime/gameplay success is not inferred from compilation or hook count.
