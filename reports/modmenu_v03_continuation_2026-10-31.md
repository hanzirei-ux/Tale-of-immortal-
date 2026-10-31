# Tale of Immortal Android — Mod Menu v0.3.1 continuation (2026-10-31)

## Current state
The v0.2 ARM64 LiteAPK Mod Menu was installed and tested by the user. Most tested gameplay controls worked; Inventory Capacity did not. The v0.3 UI/catalog source fixes existed but were not compiled.

## Progress after Work limit
- Reused v0.2 source and v0.3 Source Fix; did not restart reverse engineering.
- Updated **ModMenu.java**: new **Currency & Tokens** category for Spirit Stones, Personal Sect Contribution, City Lord Tokens, Chi You Alliance Battle Contribution, Sect Treasury and Sect Reputation.
- Updated **game_runtime.cpp**: strictly guarded currency inspector and *experimental* positive-only **Spirit Stones ADD (1..100000)** invoking only `WorldUnitData.RewardPropMoney(int moneyCount)` on the player WorldUnitData through the existing verified Unity-main-thread dispatch queue.
- Updated **jni.cpp**: backup acknowledgment is required for currency writes, but not an inspector/read-only request.
- Crucially, **no verified wallet balance readback** exists yet. SET, SUBTRACT, Unlimited, multipliers, and editing separate token/sect balances remain blocked rather than faked.
- Added `tools/report_currency_metadata.py` and a matching-metadata test. Exact metadata SHA256: `9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3`.
- Checked metadata: `WorldUnitData.RewardPropMoney` index 88717, token `0x06015A8E`, parameter `moneyCount`; `SchoolData.AddMoney` index 34366 (sect-owned), `SchoolData.AddReputation` 34367, `SchoolData.AddFaithMoney` 34368; `UnitDataProps.GetGridMaxNum` 34673 is an inventory readback candidate.
- Did **not** conflate CityToken with Chi You Alliance Battle Contribution or personal Sect Contribution with Sect Treasury.
- Host tests: 26 native test cases with 94 assertions, policy 212 assertions, catalog tests, 25 Python project tests and 10 command builder tests; plus a real-baseline metadata assertion. Native changed code passes C++17 GCC syntax check.

## Not completed / blockers
**v0.3.1 is SOURCE ONLY**: no new DEX or Android ARM64 SO compiled, no Android device validation. The execution container has Java/CMake/host C++ but not Android SDK/NDK, android.jar or R8/D8, and network DNS is unavailable. Do not rename the v0.2 binary and label it v0.3.1.

Source ZIP and compact changed-files ZIP were generated as attachments in ChatGPT's conversation on 2026-10-31; they are not yet committed here. For source build, retain the original v0.3 CI workflow `.github/workflows/build-v03.yml` which installs NDK 27c, SDK 35, and pinned Java compiler tools.

## Next steps
1. Import the v0.3.1 source attachment into the repository as code (avoid publishing proprietary game binaries, original APK, assets or personal saves).
2. Build both `toimodmenu.dex` and `libtoimodmenu.so` together in GitHub Actions.
3. Test experimental player ADD 100 Spirit Stones; verify wallet before/after and save/load. Do not claim gameplay success based on invocation alone.
4. Map wallet readback and safe SET / SUBTRACT; map personal Sect Contribution, Chi You Battle Contribution, City Tokens and clothing special-shop materials separately.
5. Verify inventory capacity via `UnitDataProps.GetGridMaxNum`; repair old `propGridNum: 52 → 52` issue.
6. Keep NPC Editor excluded and preserve all working v0.2 player cheats.
