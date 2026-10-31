# v0.3.2 — Read-only Catalog Exporter

**SOURCE IMPLEMENTED · HOST TESTED · COMPILED — NOT DEVICE VERIFIED.** User reports v0.3.1 works on phone; the new exporter awaits device testing. Previous v0.3.1 files are preserved.

- [Download DEX-only patch (55,467 bytes)](TaleOfImmortal_ModMenu_v0.3.2_ReadOnlyCatalogExporter_BinaryPatch.zip)
- [Source](source), [build](source/BUILD_V032.md), [technical report](source/PATCH_REPORT.md)
- [Indonesian install/rollback](source/README_ID.txt), [phone checklist](source/TEST_CHECKLIST.txt)
- [Next collector roadmap](source/docs/CATALOG_COLLECTOR_NEXT.md)

ZIP SHA-256: `069fa832cf0db3164bf32135f21cd4faafe2e9ad0dd6d73d471ebb9ccb4717ca`. New DEX SHA-256: `7e1f65e069785ab12ed89479c7e74cff6ad8fbcdc21351622354dea6b67a9ac9`.

Progress completed:

1. Reused pinned v0.3.1 source and validated/read all 10 supplied exporter v4 files.
2. Applied the v4 integrator; added bounded worker IO, one-page receipt routing, explicit native generation validation, cancellation, timeout and partial-file cleanup.
3. Integrated Export ALL item IDs (read-only), Cancel, progress/count/path and Android system Save JSONL into Items / Recipes.
4. Preserved exact native/JNI source, existing gameplay/resource writers, 22 menu method bodies and the original v0.3.1 SO. Protocol 4 / 19 JNI remains compatible.
5. Passed inherited suites, 47 current Python tests, original v4 tests, 90 exporter/guard/copy checks, 1,643-row synthetic JSONL validation, actual DEX/ELF/JNI and package checksum checks.
6. Compiled the new helper DEX and prepared a small DEX-only APK patch. No signed APK or phone result is claimed.

Coverage limit: this exports the current native **non-hidden ConfItemProps** catalog, which is incomplete. The ~11 Manual entries reported by the user are not the whole game's Manual system. Missing names/categories remain; unsupported translations, source keys, rarity, description and subtype are null. Separate configuration/template/Manual-instance collection is the next phase after a real phone JSONL.

Private input APKs, IL2CPP/metadata, AssetBundles, extracted game data and saves are excluded. Source and the project's own compiled helper only are published.
