# Tale of Immortal LiteAPK Mod Menu v0.3.0

This is the continuation of the user's working v0.2 integration and supplied v0.3 SourceFix. The matching helper DEX and ARM64 native library have been compiled and statically checked. **COMPILED — NOT DEVICE TESTED.**

See [PATCH_REPORT.md](PATCH_REPORT.md) for current features, actual verification and limitations; [README_ID.txt](README_ID.txt) for Apktool M installation and [TEST_CHECKLIST.txt](TEST_CHECKLIST.txt) for phone acceptance. [BUILD_V03.md](BUILD_V03.md) describes the component build.

The patch preserves v0.2's primary DEX and all original game libraries. It adds player currency/contribution/sect resource editing, effective inventory capacity edits, readable Android controls, localized paginated item browsing and independent operation receipts. NPC editors are excluded. Alchemy recipe items are filtered from actual configuration; acquiring an item does not unlock a recipe.

Only original mod development source, open-source build dependencies, static mappings, tests and reports belong in this repository. Original APKs, game binaries/metadata/assets, private saves and extracted caches are excluded. Native method indices/tokens are not runtime addresses. The archived V60 reports describe a different custom build.
