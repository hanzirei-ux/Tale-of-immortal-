# Tale of Immortal LiteAPK Mod Menu v0.3.2

**SOURCE IMPLEMENTED · HOST TESTED · COMPILED — NOT DEVICE VERIFIED.** The user reports v0.3.1 works on their phone. This release adds the supplied v4 read-only item-catalog exporter to that existing implementation and builds a new helper DEX. The v0.3.1 ARM64 SO, native hooks, JNI protocol 4 and player-only gameplay behavior are preserved.

Items / Recipes now contains **Export ALL item IDs (read-only)**, Cancel and Save JSONL. Enumeration uses the existing bounded catalog path; the completed file can be copied through Android's system document picker. No manifest or broad storage permissions are added. This is an integrated game helper, not a separate application.

**The current catalog is incomplete.** ALL means all non-hidden rows returned by the existing native ConfItemProps catalog. Separate skill/manual configuration and generated Manual instances are not collected; unresolved names and missing categories remain visible. This release prepares genuine phone JSONL for measuring those gaps. No Android-generated dump is claimed yet.

- [Installation and rollback, Indonesian](README_ID.txt)
- [Phone test checklist](TEST_CHECKLIST.txt)
- [Build instructions](BUILD_V032.md)
- [Technical report and verification limits](PATCH_REPORT.md)
- [Next collector roadmap](docs/CATALOG_COLLECTOR_NEXT.md)
- [Original supplied exporter v4](reference_exporter_v4)

The binary patch contains only `classes2.dex`. Keep the working v0.3.1 `libtoimodmenu.so`. Replace the existing helper's actual multidex slot; never duplicate helper classes or replace the primary game DEX. Use the installed APK's signing key. No original game APK, libraries, metadata, assets or saves are published.
