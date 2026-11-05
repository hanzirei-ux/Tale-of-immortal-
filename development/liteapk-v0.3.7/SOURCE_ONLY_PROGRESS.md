# Tale of Immortal Android — v0.3.7 Offline Catalog Picker source milestone

**2026-11-05 — SOURCE PREPARED / HOST CHECKED / NOT DEX COMPILED / NOT DEVICE TESTED.**

The original v0.3.6 functional Mod Menu, APK, DEX, JNI4 native methods, SO and saved games remain unchanged. This is an additive source-only design for a new standalone **Offline Catalog** page appended after the seven existing menu pages. It uses Android ACTION_OPEN_DOCUMENT to import an optional private JSONL file into app-private storage, then performs read-only name/ID/category/subtype search (40 rows/page). Selecting rows never issues gameplay/native mutation calls.

The private companion catalog, supplied directly to the user and **not committed to GitHub**, has 4,206 namespace-aware records: 3,309 native Item IDs, including 3,284 nonhidden and 25 hidden; 395 Gear (295 Outfit, 56 Mount, 34 Ring, 10 Artifact); plus 897 named Manual constructor candidates (187 save+native category verified, 710 category inferred). Item ID and Manual BaseID namespaces are never merged. Hidden items and all Manual rows are browse-only. Existing native Add Item remains on the original Items / Recipes page and must still confirm ID availability.

Development deliverables sent privately: OfflineCatalogPage.java, an assertive patch_menu_v037.py that applies only four edits to a copied original ModMenu.java (append page, add page branch, cleanup reference, update version label), optional catalog generator, test scripts, build_dex_v037.sh, README, and private JSONL file. Source ZIP and combined private ZIP were CRC-checked.

Host checks passed: 11 catalog invariants covering namespace uniqueness, counts and read-only status; synthetic source patch guard; helper Java syntax compiled against local API stubs. This **is not an Android SDK/D8 compile**. The current environment lacks pinned D8/R8 and android.jar, so **no v0.3.7 classes2.dex was produced or verified**, and **no claim is made that a patch is installable**. The historical 137,072-byte v0.3.6 DEX was left untouched. The build script explicitly requires official/pinned ECJ, D8 and SDK jar before producing a replacement DEX from the existing project source.

Next: run the pinned ECJ/D8 compile against official Android SDK 35, check 19 JNI declarations and old behaviors, then deliver versioned DEX-only patch for user phone testing. Manual reward generation remains unimplemented and excluded. Keep full source-derived catalogs and user save data private.
