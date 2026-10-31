# Tale of Immortal Android — Read-only Item Catalog Export v4

**Status: IMPLEMENTED SOURCE + HOST TESTED. NOT APK-BUILT, NOT TESTED ON PHONE.**

## What this actually does

This patch adds an **Export ALL item IDs (read-only)** button to the existing v0.3.1 in-game Items/Recipes page. The exporter reuses `NativeBridge.request("catalog", "@-1||OFFSET", 0, 0, false)` and `NativeBridge.takeGameResults()` already present in the live-source GitHub repo, with **40 items/page**. It saves JSONL under the app-specific file directory. NO new native IL2CPP hooks, gameplay mutations, inventory editing, or artificial item entries are introduced.

The exporter is strictly for **items that current `ConfItemProps`-backed catalog indexes**. It does **not yet** get all dynamic Martial/Skill Manual instances, entire `ConfLocalText` translations, special `ConfItemBook` descriptions, grade colors, or generated affixes. This first stage is designed to obtain a genuine phone-derived item dump rather than guessing names from metadata. It intentionally exports a `display_name` without claiming its language is English or Chinese. It does not make new manuals usable.

## Install into the SOURCE tree (not a patch you can install directly)

1. Download a current copy of `development/liteapk-v0.3.1/source/` from `https://github.com/Beta-Tester-mod/Tale-of-immortal-`.
2. Copy `android/bridge/src/main/java/org/npc/toibridge/ReadOnlyCatalogExport.java` to the same relative directory in that source.
3. Run `python3 tools/integrate_v031.py /path/to/source/android/bridge/src/main/java/org/npc/toibridge/ModMenu.java`. The script creates `ModMenu.java.pre_readonly_export`, rejects unknown source layouts, and does not touch native files.
4. Build Java `classes2.dex` using the **repository's existing v0.3.1 build pipeline**. Leave `libtoimodmenu.so` completely unchanged. The source patch alone is not an installable binary.
5. On Android, open the in-game Mod Menu, load a player save, open `Items / Recipes`, press **Export ALL item IDs (read-only)**. Keep the application running through the export. Successful status shows exact JSONL output path.
6. Export file should be under `Android/data/<actual-package-name>/files/toi_catalog_exports/` when external app-specific storage is available; otherwise under the app's internal `files/toi_catalog_exports/`. Exact path appears on-screen. Android 14 file-manager access to `Android/data` may be restricted; use ADB or an approved storage share/copy workflow if needed.
7. Process the JSONL on a PC with `python3 tools/build_catalog_from_dump.py <dump.jsonl> <output-directory>`. **Never publish game assets or personal save files.**

## Invariants and security

- Source change only in ModMenu.java and one newly added class; **no native library changes**.
- Existing v0.3.1 catalog UI and combat hooks remain unchanged.
- No player save writes; only an app-specific JSONL export file is created.
- Queue accepts one page at a time; per-page response must match offset/size/total, and duplicate item IDs abort collection.
- Malformed data fails closed and partial output is deleted. No false claims about skill item generation.
- Names available via existing catalog may still be fallback `item_name...` and should be resolved in a separate future localization pass.
- If runtime reloads save/world between pages, native mailbox generation invalidation should abort a pending request; the export also checks stable totals, but **stable totals alone do not prove a stable save generation**. Future runtime collector should explicitly return a snapshot generation per page.

## Host tests

Run from this source package:

```bash
javac -encoding UTF-8 -d /tmp/toi_testclasses android/bridge/src/main/java/org/npc/toibridge/ReadOnlyCatalogExport.java tests/ReadOnlyCatalogExportTest.java
java -cp /tmp/toi_testclasses ReadOnlyCatalogExportTest
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

**These tests only validate export parsing/integration transformations, not IL2CPP runtime or Android UI.** The real game remains untested for this feature.

## What must follow for all Manuals, category, rarity and descriptions

- Read `ConfMgr.get_itemBook`, `get_itemHorse`, `get_itemSkill`, `get_clothItem` through strict token/signature checks on Unity thread.
- Enumerate `ConfLocalText` via `allConfList` in **bounded batches**; do not invoke unguarded `GetText` on unknown keys.
- Read `get_battleSkillBase`, `get_battleSkillLevel`, `get_battleSkillPrefixName/Value`; exported skill templates are **not** automatically learnable manuals.
- For **actual Manual instances**, inspect valid `MartialInfoData` owned by available gameplay objects; no `NewMartial`, `Study`, stat edit, or AddItem calls during collection.
- Map verified rarity grade->color from game's rendering functions; level must not be used as a proxy.

Next critical artifact is a **real exported phone JSONL** from this first-stage button. Only then can we evaluate the current catalog's precise coverage and missing keys before adding new native collector paths.
