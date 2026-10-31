# Tale of Immortal Android — LiteAPK Mod Menu Research v1

**Scope:** Static mapping of files provided on 2026-10-30 and a safe command-preview generator. This ZIP is **not an APK**, a playable mod, a working Unity hook, or an interactive Mod Menu. No original game binaries or saves are redistributed.

## Verified baseline

- `libil2cpp.so`: SHA-256 `c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099`.
- `global-metadata.dat`: SHA-256 `9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3`, metadata v31.
- Metadata: **23,039 types**, **144,793 methods**, **90 images**.
- `data/il2cpp_target_methods.csv` lists 566 metadata method definitions from 24 selected types; method indices and tokens are **not runtime addresses**.
- `data/gm_catalog_212.csv` contains **212 command-description entries** in the managed string-literal table. Those are embedded examples; not verified runtime calls.

## Top integration candidates (all in Assembly-CSharp.dll)

| Type | Method | Metadata method index | Argument count | Why it matters |
|---|---|---:|---:|---|
| GMCmd | CMDCall | 41666 | 1 | GM dispatcher candidate |
| GMCmd | Execute | 41719 | 2 | GM command executor candidate |
| EditorCommand | Execute | 79134 | 2 | Alternate command system |
| UI_EditorTest1Cmd | QuickSelectCMD | 74551 | 1 | Existing debug UI |
| GMFunc | npctishengjingjie | 2512 | 1 | Realm editing candidate |
| UI_EditorTest6 | UpdatePlayerLockHP | 74907 | 0 | Player HP lock debug UI, not validated as global God Mode |
| UIPlayerBagExtend | get_gridMaxNum | 67339 | 0 | Bag size display state |
| UIPillFormulaView | Study | 67283 | 1 | Learning a pill recipe |
| UnitActionPropPillFormulaStudy | OnCreate | 84056 | 0 | Recipe use action |
| ConfRuneFormula | GetStudyRuneFormula | 32794 | 0 | Talisman recipe database |
| PropsArtifact | SetAttrrRate | 34143 | 6 | Artifact property editing candidate |
| ConfArtifactSpriteTalent | IsSpriteTalentUnlock | 16335 | 4 | Spirit talent unlock check |

Metadata type name and argument counts are **strong evidence of where to investigate**, not confirmation of function signature, permissible call context or gameplay effects.

## Static command preview utility

```bash
python tools/gm_command_builder.py add_exp 100
python tools/gm_command_builder.py add_player_stat hp 10
python tools/gm_command_builder.py set_npc_realm 123 5 --ack-backup
python tools/gm_command_builder.py resize_bag 10 --ack-backup
python tools/gm_command_builder.py add_item 1001 5 2 --ack-backup
python -m unittest discover -s tests -v
```

`add_item` parameters are **raw experimental parameters**; second argument is NOT confirmed as quantity. This preview tool does not call game functions or patch files. NPC/realm and bag operations require a backup acknowledgment. Destructive `qingkong` is deliberately absent.

## Investigation priorities

1. Determine exact input string/parameter formats for `GMCmd.CMDCall`, `GMCmd.Execute`, and `EditorCommand.Execute` via native disassembly and safe runtime trace. Check command entry points and thread context. Never assume metadata indices are executable pointers.
2. Confirm whether `UI_EditorTest6.UpdatePlayerLockHP` changes damage handling generally, or only toggles a debug test state.
3. For recipe manager: inspect `ConfMakePillFormula`, `UIPillFormulaView.Study`, `UnitActionPropPillFormulaStudy.OnCreate` and `ConfRuneFormula`. Separate **recipe-book inventory items**, **learned/unlocked recipes**, and **required crafting materials**.
4. For artifact manager: isolate persistent fields in `PropsArtifact` vs effects stored in combat objects and sprites. Verify after save/load.
5. For bag slots: understand command `beibao_10` semantics (absolute set vs relative add), how `gridMaxNum` is calculated, and whether inventory exceeds capacity without deleting items.
6. For NPC realm: compare `jingjienpc` path with `UnitActionRoleUpGrade`; test ordinary NPC only on backup, check skill/stat scaling, month rollover, and save/load.
7. Prepare a fresh Android packaging baseline. The provided ZIP lacks the complete manifest/resource layout; retain native Unity/JNI dependencies from LiteAPK. The separate `libandroidoyunclub.so` has native activity registrations; do not delete it blindly.
8. Only after the dispatcher is proven, build a genuinely interactive embedded native/UI mod menu. Continuous multiplier settings require player-only runtime hooks and a baseline comparison, not repeated one-shot GM commands.

## Data boundaries

Only filenames, method names, hashes, and command examples from user-supplied game components are included. Source game binaries, proprietary assets, local saves, and personal cache data are **not** included in this pack.
