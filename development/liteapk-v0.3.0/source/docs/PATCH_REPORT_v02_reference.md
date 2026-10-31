# Tale of Immortal LiteAPK Mod Menu — v0.2.0-test

Milestone date: 31 October 2026. Target: Xiaomi 11T, Android 14, ARM64; Android 11 ARM64 is an additional untested target.

**This milestone produces actual compiled/modified binary components and an integrated Android menu implementation. No feature is WORKING — DEVICE VERIFIED. No complete APK was built, signed or installed.** The missing full APK, manifest/resources and referenced unsupplied checkupdate dependency block final packaging and phone validation, not native/DEX implementation.

## Delivered artifacts and exact status

| Artifact | Bytes | SHA-256 | Status |
|---|---:|---|---|
| classes.dex | 8,696,360 | f87577df61d4f9a18f942b2fa6f594c790a209ee61af8e13625041f84692c4ea | COMPILED — RUNTIME UNTESTED |
| toimodmenu.dex | 32,784 | 422aca4048036aed977b42bff202711ff42473338ef052778e64df89a56ee43e | COMPILED — RUNTIME UNTESTED |
| lib/arm64-v8a/libtoimodmenu.so | 582,616 | d70ce2a1bddb304afacae883bb2ce8a95fe6aaa3da47aea382b23712bd9d5385 | COMPILED — RUNTIME UNTESTED |

`patch/patch_manifest.json` records exact component hashes and baseline guards. `SHA256SUMS.txt` covers the delivered project files. The primary game DEX is a private derivative of the supplied DEX; it must not be published. Original game IL2CPP/Unity/startup libraries, metadata, assets and saves are omitted. Original input files remain unchanged separately.

The native library installs a Unity callback and 14 gameplay/lifecycle adapters, for an expected total of 15 hooks. The UI exposes 22 native settings: 18 combat controls and four EXP controls. Two are native critical ratings, not the requested critical percentages. There are also real player base-stat operations, item catalog/reward actions and a small allowlisted GM utility group. Each operation reaches a game method or player-owned native value path; no placeholder button reports a simulated game-state change.

The feature table is `FEATURE_STATUS.csv` (62 rows). It deliberately separates compiled controls from the broader features they do not yet fulfill. Seven policy entries remain reserved for later adapters and have no active UI. Capabilities expose only installed adapters; unsupported settings are masked out on the Unity thread and rejected by the UI JNI setting entry point.

## Continuity and baseline verification

The v0.1.0 bridge, hash implementation, IL2CPP runtime API resolution, command queue, metadata parser, target mapping, research pack and host tests were reused. The old documentation/evidence is retained under `history/v0.1.0` and is not the current feature report. Its statement that no game extraction was available has been superseded by the newly attached ZIP.

`tales.zip` was opened, CRC checked and selectively extracted: 147,069,779 bytes, 9,006 entries, no CRC failure. Archive SHA-256:

`9db324ea58a89426fa3533bea4dd9e636e316d5eed54188ea6de1581415290d8`

| Original input | Bytes | SHA-256 |
|---|---:|---|
| libil2cpp.so | 144,951,312 | c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099 |
| global-metadata.dat | 42,923,616 | 9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3 |
| classes.dex | 8,612,260 | 38d329e62ef2d0d37e07b41289f00733f1243e817f4418012903bbb2411b3c2c |
| libandroidoyunclub.so, separate attachment | 950,304 | 0cafd642bf5f1d97b4b09976c4d08ed55255e20962727da9f78b0943b44c6b1a |

Metadata version 31 was parsed against this library. The structurally recovered Assembly-CSharp module is RVA `0x7ddd0e0`, with method pointer table `0x83fdee8` and 97,514 entries. These are independently recovered current-binary values, not old V60 addresses. Method tokens index that module; metadata method indices are never executed as addresses. Il2CppDumper 6.7.46 emitted a possible-protection/JNI_OnLoad warning, then completed metadata/code/struct generation. Its terminal ReadKey failed after all outputs were written because no interactive console was attached. The recovered code table was also independently validated structurally rather than trusting that warning or the dumper alone. The 28 selected method signatures/RVAs/file offsets/prologue fingerprints are in `native/baseline_profile.json` and were checked against executable mappings of the actual supplied file.

The historical V60 report records a different library hash (`b115635f…`) and size 144,968,752; it reports the same metadata hash. No V60 patch bytes or RVA table were restored. Without an official clean matching library, the current distributor's gameplay changes cannot be exhaustively distinguished from original game code. Matching the supplied LiteAPK fingerprint does not certify it as an official or trusted release.

No AndroidManifest/resource project or complete original APK was present. Twenty-one private-path entries were skipped by selected extraction. No extracted private world cache/save data is bundled or uploaded publicly.

## Corrected GM ABI and verified debug path

The v0.1.0 runtime resolver required a static dispatcher as a fail-closed hypothesis. The actual current binary disproves that hypothesis: **GMCmd.CMDCall is an instance void method**. This milestone corrects that check and creates/roots a proper GMCmd object using `il2cpp_object_new`, then invokes its verified parameterless constructor.

| Method | Current ELF RVA | Verified signature / role |
|---|---|---|
| GMCmd.CMDCall | 0x452e16c | instance void (string), token 0x0600a2c3 |
| GMCmd constructor | 0x4581390 | instance parameterless ctor, token 0x0600a2f6 |
| GMCmd.Execute | 0x45816e0 | instance void (string, string[]) |
| UI_EditorTest1Cmd Init input closure | 0x5018d4c | receives InputField[]; direct BL to CMDCall at 0x5018efc |
| UI_EditorTest1Cmd.QuickSelectCMD | 0x5018208 | input-selection helper; not the dispatcher |
| SchoolBigFight.EditorCommand.Execute | 0x52ab258 | static void (string, string[]), separate subsystem |
| UnitySynchronizationContext.ExecuteTasks | 0x7d221b4 | static void callback with MethodInfo* ABI |

The existing UI constructs GMCmd in its constructor and its Init closure calls CMDCall. CMDCall splits commands and can route to its reflection Execute method (call at `0x4549c94`) or the separate SchoolBigFight command subsystem. Evidence is in `evidence/gm_call_path_v02.json`. The new menu uses a constructed GMCmd through `il2cpp_runtime_invoke`, avoiding screen taps or an assumed initialized console UI. Managed exceptions produce error receipts; a void return is explicitly `INVOKED_UNVERIFIED`, not proof of an actual gameplay effect.

The new request queue is bounded to 32 entries, one processed per verified Unity callback, with a 10-second TTL and world/player generation cancellation. Persistent requests require a user backup acknowledgment. Unity thread identity is verified from the actual Unity SynchronizationContext and managed main-thread ID, not from Android's UI thread or a GL rendering queue. Initialization stops after 120 failed context callbacks rather than polling indefinitely. All menu-triggered game object operations run there.

Only allowlisted player commands are accepted. `qingkong`, NPC-target commands, arbitrary manual GM text and optional NPC arguments are not exposed or accepted. The inherited research catalog remains reference data only. The original bounded probe bridge still exists and is pumped by the real Unity callback; the multi-feature menu's requests use the new typed queue.

## Native gameplay behavior

Each hook checks the mapped prologue against the current profile before Dobby installation and rejects a reported success when the entry bytes did not actually change. The on-disk game library is unchanged. When Android loads IL2CPP directly from the APK, the cached hashed library is checked against all executable mapped segments before hooking. When it is extracted, the loaded file identity must match the hashed file. Critical field layouts are checked through runtime reflection before gameplay adapters activate. ASLR base is resolved with loaded ELF information.

Player combat identity requires exact `UnitCtrlPlayer` class identity and its world-unit reference equal to `g.world.playerUnit`. NPC classes, allies and enemies pass through the original functions. World/skill EXP and stat/item requests are similarly bound to the current player's actual owned data. DLC subclasses and player summons are not implicitly included.

- **God Mode:** suppresses negative player AddHP damage and skips player Die. **Unlimited HP** also refills current battle HP to computed max on the Unity callback. It does not claim protection from every scripted non-HP death path.
- **Unlimited Energy / energy cost:** refill player battle MP and suppress or scale negative MP changes. The factor includes non-skill drains routed through AddMP; it is not a selected-skill cost editor.
- **Damage:** edit the signed final HitData HP delta only when its attacker is the actual player. The original hit value is restored after the original call, and a thread-local nesting guard prevents repeated modification of the same HP call chain.
- **Category precedence:** enabled Ultimate (same ultimate object), then any enabled Skill for hits carrying a skill object, then Spiritual, then Martial, otherwise All. A basic attack carrying a SkillBase object can also be a Skill hit. With category override, All ×10 + Martial ×5 gives ×5. Explicit combine gives ×50. Critical multiplier applies only when the game already marks the hit critical; the final combined factor is capped at ×100.
- **Defense/resistance/movement:** bind only player battle DynInt objects; scale values through int/float getters with a shared nesting guard. World stats are deliberately excluded from these runtime getter bindings to avoid copying an already-scaled world value into battle and scaling it again.
- **Critical controls:** absolute `crit` and `guard` rating overrides, range 0..100, plus final critical-hit damage factor. A percentage chance formula/inverse and critical-defense damage factor are not implemented.
- **Attack speed:** divide the player's returned skill shot interval DynInt by the factor. This is a shot-cadence adapter, not a universal animation-speed override. Cooldown scales player-owned SkillDataAttack's returned cooldown; other skill families/cached timers require device checks.
- **EXP:** positive player PropertyData AddExp/AddFixExp gains share a nesting guard. Cultivation-spot OnCreate wraps its direct AddExp path. Manual-training OnCreate wraps the player's AddMartialExp call; other player AddMartialExp calls use Skill EXP. Global and category factors use the same override/explicit-combination policy, cap ×100, and pass through original realm/cap handling. Loss/spend values and NPC gains are unchanged.

Runtime settings are copied once per Unity callback under a mutex. Hot DynInt hooks use a thread ID fast path and skip binding scans when no relevant modifier is enabled. Binding storage is reserved and bounded; there is no repeated catalog scan on a frame. The UI polls diagnostic text at most once per second while visible. Initialization/hash work runs on one worker thread; it never dispatches gameplay there. Native C++ symbols are hidden and static-library symbols excluded from exports, retaining the intended JNI/C API boundary.

Dobby is vendored at commit `9c85e74f92eda36b99ddb0fddb17a9df2278a4d3`, statically linked. `third_party/Dobby/LOCAL_FIXES.patch` records bounded debug hex formatting and maps-reader EOF/truncation handling/macro cleanup. Its Apache license and static C++ runtime notices are included. These are small local source fixes, not claims of a device-tested hook engine.

## Base-stat, inventory, item and utility implementation

The stat editor accepts SET/ADD/SUBTRACT/MULTIPLY and reads back the actual DynInt base. Forty-two allowlisted fields cover HP/MP, attack/defense, crit/guard and their values, native `phycicalFree`/magicFree, movement, luck, lifespan, health/energy/mood, talent/ability points, 12 martial/spiritual bases, six crafting/knowledge fields and inventory base slots. Raw game field names are shown to avoid inventing uncertain attribute translations. Arbitrary offsets/fields, realm, identity, story flags and NPC targets cannot be entered.

Edits invoke the actual DynInt base getter/setter and honor the game's min/max getters plus conservative build limits (normally 0..10,000,000; HP max/life at least one). This ceiling is input validation, not proof that every large value is gameplay-safe. Use small changes first. Save persistence and a complete restore are unverified; base setters may have game-managed callbacks and subsequent recalculation can change derived values. No direct save-file patching or automatic game-save operation is performed.

`beibao_10` was traced in this exact binary: it reaches `g.world.playerUnit.data.dynUnitData.propGridNum` and calls DynInt.AddValue with an additive delegate, **not an absolute capacity setter**. It may stack and its save persistence is not established. The menu therefore uses the base-stat setter on `propGridNum` for SET or ADD, capped at 2,000 base slots and rejecting reductions. Ring/other capacity bonuses remain part of the game's derived capacity. This does not expand the five combat item/equipment slots. Inventory accessibility and save/load still require phone tests.

Item search reads the loaded `ConfMgr.itemProps` list, checks list/array bounds and excludes hidden rows. Results show real IDs, names/name keys, type and level, at most 60 per query. Types derive from the actual game enum, including pills, manuals, equipment, materials and other recipe books. Names may be localization keys; English translations/icons are not synthesized. Add Item validates a digit-only actual catalog ID, quantity 1..9,999 and stackability, then invokes the player's `WorldUnitData.RewardPropItem(int,int,bool)`. Non-stackable requests are limited to one item per action. Quest/special items are not certified safe merely because they appear in this catalog.

Recipe books can use that same acquisition route. Dedicated recipe configuration/search, learned-recipe unlocking, requirements and crafting modifiers are not implemented, so there is no pretend Unlock or Craft button. Adding a book is not reported as unlocking its recipe.

Additional allowlisted commands cover small custom EXP, stamina recovery, learning manuals in the player's bag without the optional NPC parameter, max manual cultivation, max bag manual entries, grade-1 breakthrough materials, player artifact repair, Bagua Jade protection points and Eye of Providence skill unlock. Static command traces show the player-data path for the manual/repair commands. `tupocailiao_1` calls `GetGradeUpQuality(1)` and is labeled grade-1 assistance, not a current-realm missing-material solver. Artifact spirit attributes, Gourd editing, selected-skill/destiny/trait/Dao Heart editors and all NPC editing/AI/progression remain absent.

## Android integration and third-party dependency review

The authoritative actual DEX was disassembled, rather than trusting an arbitrary smali folder in the extraction. Only OverrideActivity gains onCreate and onDestroy overrides. onCreate first calls the original registered native UnityPlayerActivity.onCreate, then installs the menu. onDestroy detaches/cancels/resets the menu, then calls the original native parent. Mod attach/detach exceptions are logged under TOIModMenu while the original native parent lifecycle remains callable. Both original parent signatures and every other original class's disassembly are unchanged.

The helper is a separate compiled DEX so it does not collide with the primary game's method references. The native facade loads `toimodmenu`. The English menu has a movable saved-position TOI launcher, category pages, switches, sliders/numeric fields, search, apply/read/reset and explicit saved-configuration loading. The panel consumes touches; hidden space outside the launcher does not take gameplay input. Launcher elevation/clamping is implemented, but actual landscape rendering, display cutouts and Unity surface order have not been observed on a phone.

The startup library has 124 decoded JNI registration groups / 469 methods, including the Unity activity group. Its native parent lifecycle is preserved. Its hash/imports/registration strings were audited statically; no writable-executable ELF segment was reported, and no plaintext checkupdate reference was found there. `PrivacyActivity` in the actual DEX does call `System.loadLibrary("checkupdate")` and registers group 0x25 (37). All six method names/signatures match that group in libandroidoyunclub. `libcheckupdate.so` itself was not supplied, so its behavior/security cannot be audited. Preserve this load and the library if present in the full APK; whether this privacy Activity lies on the launcher route is unknown without the manifest. See `evidence/startup_dependencies_v02.json`. A static review is not a malware verdict or proof of all dynamic behavior; signing provenance and distributor runtime changes remain unknown. The library is neither removed nor described as a confirmed gameplay cheat.

## Validation performed and remaining blockers

- Host bridge: 26 test cases / 94 assertions PASS.
- Shared modifier policy: 212 assertions PASS, including wrong owner/world, OFF behavior, explicit category combination/cap, malformed numeric inputs and concurrent settings.
- Python: 24 current analysis/installer tests plus 10 inherited research tests PASS. The nine installer cases use synthetic fixtures and include AXML parsing, launcher aliases/indirection, signature-file handling, preserving original bytes/dependencies, multiple DEX placement, alignment and rejecting wrong baselines/modified patch components.
- Host AddressSanitizer + UndefinedBehaviorSanitizer: both bridge and policy suites PASS with leak detection disabled. This is neither a device sanitizer test nor a leak-free claim.
- Actual ARM64 Release/strip build PASS; Java ECJ, D8 and original game smali rebuild PASS. A clean native build and final rebuild logs are included; only CMake legacy-policy deprecation notices remain, with no compiler warning in the clean/final build after the local Dobby fixes.
- Static artifact verification PASS: 28 game profile sites, 15 JNI entry points, AArch64 ELF protections/dependencies, two valid non-overlapping DEX files and preserved original method signatures.

The DEX SHA-1/Adler32, file bounds, class sets, original method/native signatures, helper class separation and 15 JNI exports were checked. Original 8,569 classes remain. All re-disassembled classes except OverrideActivity are textually identical; the Activity difference is precisely its two added lifecycle methods and normal method reordering. The own native library is AArch64 ELF, system-only dependencies, 16 KiB LOAD alignment, RELRO and non-executable stack. This does not establish the original game's 16 KiB-page compatibility.

Known limitations:

- Full game Android manifest/resources/assets and original signing information are missing. The installer is tested on synthetic APK fixtures, not the full game APK. Launcher routing and signature/protector acceptance must be verified from that APK.
- No Android device/emulator installation, startup, menu rendering, combat, save/load, performance or month-transition test was performed. All 49 phone checks are NOT RUN.
- Two critical rating controls do not fulfill percentage editors. Skill/ultimate classification, shot cadence, cached timers, DOT/reflection/summon behavior and save persistence require measured phone tests.
- Combat bindings are captured by player initialization and incoming HP paths; initializing after an already-started fight can require re-entering combat before all derived modifiers bind. Unsupported DLC player subclasses fail player identity checks rather than affecting another unit.
- Base-stat/GM changes may persist through the game's own save flow; Reset disables runtime modifiers but cannot undo already healed resources, added items, unlocked skills or saved edits. Automated verified restore is absent.
- Many requested crafting, artifact-spirit, selected-skill/destiny utilities, inventory removal/quantity editing and compatibility features are not implemented. They are listed explicitly in FEATURE_STATUS.csv and not represented by working-looking buttons.
- A direct-from-APK initialization can temporarily occupy about 188 MB of private cache storage for verified copies; no equivalent large buffer is held in RAM.

Next concrete steps: integrate these compiled components into the complete matching original APK; verify its actual launcher and signing/update constraints; run the initial safe one-shot checks, then all combat/EXP/UI tests in the same installation using a backup save; inspect failures and adjust only the responsible adapters. After device validation, continue dedicated recipe unlock/material discovery and artifact-specific methods independently. NPC work remains deferred.
