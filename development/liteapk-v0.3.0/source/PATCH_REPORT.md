# Tale of Immortal LiteAPK Mod Menu v0.3.0

The new `classes2.dex` and ARM64 `libtoimodmenu.so` have been compiled and packaged together. They extend the existing v0.2 menu and the supplied v0.3 SourceFix. **Status: COMPILED — NOT DEVICE TESTED.** No complete APK was rebuilt, signed, installed, or tested on a phone in this milestone.

The small patch replaces only the existing helper DEX and native mod library. The v0.2 main `classes.dex`, original `libil2cpp.so`, startup/protection libraries, game assets, package identity and save files are not patched on disk. Player/NPC identity rules and all existing combat/EXP hook bodies remain unchanged. NPC editors remain excluded.

## Deliverable and build

| Component | Bytes | SHA-256 |
|---|---:|---|
| classes2.dex | 50,212 | `58d83b11105cb758f2f7d9cfc1cf5a877e704824b1dab549d3b795c02e3d9c39` |
| libtoimodmenu.so | 656,352 | `3f5b118cebad5a9517e837e830ef12fc9be5d7659c64bcfb29a9eee63b7ec842` |

`TaleOfImmortal_ModMenu_v0.3.0_Binary_Patch.zip`: **281,242 bytes**, SHA-256 **`af2cfe42813187819b39fd3f853a3fb280860cacb76ce221602ad8211fa79985`**. The ZIP also contains Indonesian installation instructions, component checksums, a phone checklist and required third-party runtime/license notices. It contains no original game DEX, game libraries, metadata, assets or saves.

Build tools: NDK r27c (27.2.12479018), Clang 18, CMake 3.31.6, C++17, ARM64 API 23, static C++ runtime, 16 KiB ELF LOAD alignment; Java 17, ECJ 3.38.0, Android platform 35 and D8/R8 8.7.18, helper DEX version 035 with min API 23. Dobby remains pinned to the revision and local fixes supplied by the existing project.

The binary components have no standalone APK certificate. Repacking requires signing with the same key as the installed v0.2 APK. The original LiteAPK certificate was not provided/verified. Android 11 ARM64 is a compatibility target; Xiaomi 11T Android 14 remains the principal phone test target. Neither was tested here.

## Inventory capacity repair

On this exact baseline, the delegate implementing the `propGridNum` base setter consists of `ret`. It does not write capacity. The old unchanged base readback was not proof of a successful edit. The `beibao` route attaches an additive runtime value callback and is not used as the persistent capacity editor.

The new editor stores a player-specific integer in `UnitInfoData.objData` under `toimodmenu.v03.capacityBonus`, using the game's `DataObjectData.SetString(string,int)` and `GetInt(string,int)`. That object is part of normal player serialization. No external save file is rewritten. The existing DynInt getter adapter adds the bonus only for the current player's exact `propGridNum` object on the verified Unity thread.

READ uses `UnitDataProps.GetGridMaxNum()` and `GetGridCurNum()`. SET/ADD/SUBTRACT plans edits against effective capacity and occupied slots. The existing bag plugin can double the DynInt result; its observed factor is accounted for so ADD 50 requests exactly 50 effective slots. Unknown formulas and incompatible odd increments fail closed. The editor reads the stored bonus and effective capacity after writing, rolls back a mismatched bonus when possible, and never reports unchanged capacity as a successful increase. It does not delete item records. The supported edit ceiling is 2,000 slots.

Open player inventory views are refreshed through owner-checked `UIPlayerBagExtend`, `UIPlayerPorp` and mobile `UISwitchPlayerBagPorp` update methods. Reopening a different bag view may still be needed. Save/load persistence has static storage-path evidence and still requires device testing. Reset runtime controls does not erase the persistent capacity bonus. Reverting to an older library before items fit the old capacity can hide access to expanded slots; use the explicit capacity editor and protect items before reverting.

## Currency & Contribution editor

Every resource has READ, SET, ADD and SUBTRACT, actual before/after readback, nonnegative whole-number validation and overflow/overspend protection. Transactions run once on the Unity thread. No per-frame currency additions or NPC balance edits are implemented.

| UI resource | Actual storage/path | Scope and limits |
|---|---|---|
| Spirit Stones / player money | `PropsIDType.Money = 10001`; `RewardPropMoney(int)` / `CostPropItem(int,int,bool)` | Current player, Int32; edit ceiling 2 billion |
| Personal Sect Contribution | `PropsIDType.SchoolMoney = 10011`; `RewardPropItem` / `CostPropItem` | Current player; not sect treasury; requires sect membership |
| City Token | `PropsIDType.CityToken = 10041` | Current player's item currency |
| Immortal Store Token | `UIImmortalStore.TokenPropID = 10051` | Separate store token; native store refresh reads this ID from the player's prop data |
| Sect Funds | `DataBuildSchool.SchoolData.money`, `AddMoney(long)` | Player's current sect treasury, Int64; edit ceiling 1 trillion |
| Sect Reputation | `SchoolData.reputation`, `AddReputation(int)` | Player's current sect, Int32 |
| Sect Faith Currency | `SchoolData.faithMoney`, `AddFaithMoney(long)` | Player's current sect, Int64 |

The four personal currency identifiers were verified from v31 metadata defaults. All new method tokens/signatures were checked against the matching binary/type registration. Tokens and metadata indices are not executable addresses. Runtime calls resolve through public IL2CPP APIs and require matching token, parameter types, return type and static/instance convention.

Sect edits resolve `WorldUnitData.get_school()` from the player, display the sect name/ID, and require a READ of that sect before applying. World/data-generation changes cancel pending requests; a new save/sect needs a new READ. Arbitrary target sect IDs and NPC targets are not accepted.

`totalSchoolMoney` is a lifetime earned counter, `playerPostMoney` has a different meaning, and Achievement is not assumed to be an interchangeable spendable balance. They are excluded as editable currency choices. Normal contribution awards can increment lifetime earned counters and progression; the contribution award path rejects lifetime-counter overflow. Reducing a balance does not undo earned progression.

Some original sect methods update a resource before attempting UI refresh. If the managed refresh then throws, the bridge preserves the exception and reads the actual balance. A committed exact edit returns APPLIED_WITH_WARNING, rather than inviting an automatic retry/double award. A mismatch returns FAILED with observed values. Individual gameplay/store and save/load semantics remain to be verified on device.

Unlimited balances and gain/spending multipliers are NOT IMPLEMENTED; they were optional and no unverified hooks were added.

## Catalog, contrast and exception handling

The existing v0.3 paginated browser is retained and completed: 40 selectable rows/page, category filters, live debounced search, prefix-before-substring ordering, case-insensitive ASCII matching, ID/English/Chinese/key matching, preview, quantity validation and explicit confirmation before Add Item. The catalog indexes actual nonhidden item configuration in bounded Unity-thread chunks. It caches native English and Chinese localization results; unresolved names fall back to available game data rather than invented names.

The Recipe filter covers verified Alchemy recipe books: native `AddPillFormulaOptions` looks up `makePillFormula` by `propsItem.id`; the filter intersects those actual configuration IDs with the actual item catalog. Forge/Talisman recipe-specific filtering and recipe unlocking are NOT IMPLEMENTED. They remain available through general item browsing if represented there. Adding a book is not treated as learning a recipe.

Labels, EditText, Spinner rows/popups, buttons, sliders, checkboxes, errors and confirmation dialogs use light foreground colors and opaque dark surfaces. Menu launcher, lifecycle, position persistence and touch behavior remain based on the working integration.

Requests now have individual IDs and typed receipts with operation/key/generation. A catalog result cannot overwrite a currency/stat result. Superseded searches are discarded. Polling runs only with the panel visible, with faster polling while awaiting responses. The queue remains bounded with the existing 10-second expiry. Large first-time catalog indexing can expire; resubmitting continues the cache and does not repeat persistent edits.

Player/config initialization checks prevent calls against missing owners. Managed exceptions include operation, method, exception detail and stack in the result/diagnostic log. The Diagnostics page can copy the last operation/error. The original reported NullReferenceException had no operation/stack attached, so its exact earlier cause could not be reproduced here. Complete absence of runtime exceptions is not claimed.

## Validation actually performed

- All three uploaded ZIPs passed CRC and matched the recorded SHA-256 values.
- Current game library: `c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099`, 144,951,312 bytes. Metadata v31: `9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3`, 42,923,616 bytes. Neither was modified.
- 27 new checked method specifications match current binary/metadata signatures; four currency constants, required IL2CPP exports and the no-op capacity setter were verified.
- The supplied profile's 28 native target prologues match the current executable mappings. Existing combat/EXP bodies, modifier policy and baseline profile are unchanged.
- Existing host suites passed: 26 core cases / 94 assertions, 212 policy assertions, catalog tests, 24 existing Python tests and 10 inherited research tests. Three additional synthetic APK replacement tests also passed: actual helper-slot replacement, component checksum rejection, and old-native mismatch rejection.
- New host editor suite passed 215 checks: amount boundaries, exact +50/+100/+200 capacity plans including the x2 plugin, occupied-slot protection, bounded concurrent receipts, strict method/signature rejection, managed error context and search/query handling. These tests do not simulate actual gameplay.
- DEX header, SHA-1, Adler32, classes and native signatures validated. The retained v0.2 primary DEX has no duplicate helper classes; original native registration signatures remain unchanged. All 17 Java/native JNI signatures match the actual compiled helper pair, protocol version 3.
- ARM64 ELF, system-only shared dependencies, 16 KiB alignment, RELRO and non-executable stack validated. Both binaries differ from v0.2.
- ZIP CRC and all packaged component hashes verified after assembly.

No device, installation, runtime initialization, gameplay, save/load or long-session stability test was performed. The user's previous v0.2 test reports apply to v0.2 only. New controls and fixes require the supplied phone checklist.

## Feature statuses

| Feature | Status |
|---|---|
| Integrated helper/native pair, contrast and receipts | COMPILED — NOT DEVICE TESTED |
| Capacity READ/SET/ADD/SUBTRACT, player objData bonus, UI refresh | COMPILED — NOT DEVICE TESTED |
| Seven resource editors and before/after verification | COMPILED — NOT DEVICE TESTED |
| Item browser/localization/autocomplete and Alchemy recipe filter | COMPILED — NOT DEVICE TESTED |
| Managed exception context and initialization guards | COMPILED — NOT DEVICE TESTED |
| Existing combat/EXP code preservation and compatibility checks | STATIC VERIFIED |
| Gameplay regression, persistence and Xiaomi/Android 11 compatibility | NOT DEVICE TESTED |
| Forge/Talisman recipe filter/unlocks; optional unlimited currencies | NOT IMPLEMENTED |
| NPC editors | NOT IMPLEMENTED — excluded from this milestone |
| Signed installable APK | NOT IMPLEMENTED — binary patch delivered for existing v0.2 APK |

Use `README_ID.txt` / `INSTALL_INSTRUCTIONS.md` and `TEST_CHECKLIST.txt`. First phone tests should use small money/contribution awards, the three requested capacity increments, category/search/select/Add Item, and save/load. Preserve the working v0.2 APK and a verified save backup.
