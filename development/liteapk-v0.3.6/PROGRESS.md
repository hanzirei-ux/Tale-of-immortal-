# v0.3.6 — DEX-first Full Catalog schema

**SOURCE IMPLEMENTED / HOST TESTED / COMPILED — NOT DEVICE VERIFIED.** Full native table collection remains **PARTIALLY IMPLEMENTED / BLOCKED_NATIVE**; no new SO is included.

- [DEX-only patch (68,221 bytes)](TaleOfImmortal_ModMenu_v0.3.6_FullCatalog_DEXOnly_BinaryPatch.zip)
- [Raw replacement classes2.dex](classes2.dex)
- [Source](source), [technical report](source/PATCH_REPORT.md), [native blocker](source/docs/NATIVE_COLLECTOR_BLOCKER_V036.md)
- [Install/rollback, Indonesian](source/README_ID.txt), [phone checklist](source/TEST_CHECKLIST.txt), [build](source/BUILD_V036.md)

ZIP SHA-256: `75d988db79166ba07a0b3aa5499931d25e6f4866689e1566acef4a72e88acfae`. DEX SHA-256: `d79db2a4171dcf268a85e0289ddb224577325366ccdfd5355e5134b323c7dbe3`. Retain the exact existing v0.3.1/2 SO; protocol 4 / 19 JNI methods are unchanged.

Completed: reused pinned v0.3.2, validated actual 3,284-ID phone dump, implemented full provenance schema/reference protection/progress and parser/merge, retained the legacy export byte-for-byte in host comparison, verified 14 global metadata schemas/6 enum constants/30 method contracts, passed 80 Python and Java/native regression suites, and compiled the new helper DEX.

Native JNI4 only returns ID/display name/raw type/level for non-hidden items. The new button cannot read unexposed Realm/rarity/descriptions/language/skill/manual values; metadata definitions are kept distinct from real configuration data. A 3,313-record host replay preserved all 3,284 IDs and 60 unresolved names, with no fabricated Realm/Manual rows. New Android execution remains pending. No APK or raw game asset is requested/published.

The referenced v0.3.4/v0.3.5 research ZIPs were not accessible; no inspection is claimed. Previous stable directories remain rollback references.
