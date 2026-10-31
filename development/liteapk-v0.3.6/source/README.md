# Tale of Immortal LiteAPK Mod Menu v0.3.6

**SOURCE IMPLEMENTED / HOST TESTED / COMPILED — NOT DEVICE VERIFIED.** The main deliverable is a DEX-only update over the working v0.3.2 menu. Native gameplay code and SO remain unchanged.

**Full native collection is PARTIALLY IMPLEMENTED / BLOCKED_NATIVE.** The current JNI4 catalog transmits only ID, displayed name, raw type and level for non-hidden items. This update implements a full provenance schema, metadata definitions, 3,284-ID protection, progress and normalization/merge for everything actually accessible. It does not pretend Java can read the unexposed Realm/rarity/skill tables. Read [COLLECTOR_LIMITS.txt](COLLECTOR_LIMITS.txt).

- [Installation/rollback, Indonesian](README_ID.txt)
- [Technical report](PATCH_REPORT.md) and [native extension blocker/contract](docs/NATIVE_COLLECTOR_BLOCKER_V036.md)
- [Build/test](BUILD_V036.md), [phone checklist](TEST_CHECKLIST.txt)
- [JSON Schema](schema/full_catalog_v036.schema.json), [parser/merge](tools/normalize_full_catalog.py)

Items / Recipes preserves the old exporter and adds **Export Full Catalog**, percentage/current table/item/record count, Cancel and Save JSONL. Unsupported values remain null with evidence statuses. The supplied real phone dump contains 3,284 unique IDs and 60 unresolved names; host replay preserves all IDs and the legacy export format. It is not a new Android execution test.

The original v0.3.1 and v0.3.2 repository directories remain rollback references. The v0.3.4 preparation and v0.3.5 validation ZIPs mentioned by the user were not available in the attachments, repo or file search, so no inspection of those archives is claimed. Work reuses accessible v0.3.2 code and verified binary/metadata research.

No full APK is needed or produced. The patch contains one APK replacement, classes2.dex. Retain the known v0.3.1/2 SO (SHA-256 ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729), original primary DEX and game assets. No raw game inputs or private dumps are published.
