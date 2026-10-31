# Collector phase 2 — skill/manual and enriched item metadata

The first-stage v4 implementation is a Java **consumer** of the existing read-only catalog request. It is **not** a new game-memory reader. For all manuals, phase 2 must add a native exporter (implemented only after actual device testing).

Mapped source paths, metadata tokens from `TOI_Runtime_Catalog_Research_v3`:

| ConfMgr getter | token | target table |
|---|---|---|
| get_itemProps | 0x060004D4 | ConfItemPropsBase / ConfItemPropsItem |
| get_itemBook | 0x060004DE | ConfItemBookBase / ConfItemBookItem |
| get_itemHorse | 0x060004DF | ConfItemHorseBase / ConfItemHorseItem |
| get_itemSkill | 0x060004DC | ConfItemSkillBase / ConfItemSkillItem |
| get_clothItem | 0x06000232 | ConfClothItemBase / ConfClothItemItem |
| get_localText | 0x060002CF | ConfLocalText / ConfLocalTextItem |
| get_battleSkillBase | 0x06000406 | ConfBattleSkillBaseBase |
| get_battleSkillLevel | 0x0600042F | ConfBattleSkillLevelBase |
| get_battleSkillPrefixName | 0x06000404 | ConfBattleSkillPrefixNameBase |
| get_battleSkillPrefixValue | 0x06000403 | ConfBattleSkillPrefixValueBase |

Never use tokens as native RVAs. Validate method owner, signature, token and class layout on the live baseline. Collect per-frame bounded slices on the verified Unity callback, snapshot generation tied to world; do not store unrooted managed object pointers across frames if GC can move them. Serialize into bounded pages with a source table identifier and verified `snapshot_generation`. Java writes app-private file via safe pagination and only after all record checks. Do not derive any grade color from `level` or from undocumented conventions. Keep the public source repository free of the game's proprietary raw assets and save files.

No new method hook is needed to *read* configuration if the appropriate getter and list methods can be resolved through existing `ManagedAccess`. No action mutating `PropsData` is part of this roadmap.
