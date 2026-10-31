# v0.3.2 — Read-only Catalog Exporter

**SOURCE IMPLEMENTED · HOST TESTED · COMPILED — NOT DEVICE VERIFIED.** The user reports the v0.3.1 menu/gameplay build is working on their Android phone. This milestone continues that source; it does not independently re-test that phone or claim the new exporter is device verified.

## Deliverable

`TaleOfImmortal_ModMenu_v0.3.2_ReadOnlyCatalogExporter_BinaryPatch.zip` — **55,467 bytes**. Contains only the new helper DEX plus instructions, changelog, checklist, checksums and notices. No SO, primary game DEX, APK, game assets, metadata, AssetBundles or saves are included. No complete APK was signed, installed or launched here.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Binary patch ZIP | 55467 | `069fa832cf0db3164bf32135f21cd4faafe2e9ad0dd6d73d471ebb9ccb4717ca` |
| New helper `classes2.dex` | 86436 | `7e1f65e069785ab12ed89479c7e74cff6ad8fbcdc21351622354dea6b67a9ac9` |
| Required installed v0.3.1 SO, unchanged and excluded from ZIP | 711848 | `ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729` |

DEX compile-source revision: `1077d91ad1ebc96ef31cc9eb264dc0a0a29b456b72a3b818bda598210b62a35d`. Native provenance remains v0.3.1 commit `069f30c01227dd2ecdc5fab63bfafb17243bf1c2`, original native build revision `1fe1aed4e1cd614e6f13086c8e68755a5bd3ae8e6bab1a9be5aef367ab6ecefd`. A newly compiled native library or shared new Java/native source revision is deliberately not claimed. JNI protocol remains **4 / 19 unchanged native methods**.

## Existing implementation reused

The entire GitHub v0.3.1 source was fetched at the pinned commit. The supplied exporter ZIP has 10 files, CRC PASS and SHA-256 `884f68302b2da27c329ace6447c803d0e02c450a3b6659f81b847938dd334b98`. Every source, test, mapping and documentation file was read. Its original `integrate_v031.py` was applied once to the actual v0.3.1 ModMenu, then the inserted exporter was hardened in place. `reference_exporter_v4/` retains the original supplied implementation/tests unchanged. `ReadOnlyCatalogExport.java` and the dump-to-CSV builder are reused and extended rather than replaced with a parallel application.

The v4 integrator alone did not provide cancellation UI, Android file retrieval, worker file IO or exact cross-page world-generation checks. Its writer also lacked explicit unknown/fallback/source-table fields and robust cleanup after a failed close. These are completed in the integrated implementation.

All 26 native files and the NativeBridge declarations are byte-identical to v0.3.1. The ARM64 SO is byte-identical. Twenty-two existing menu method bodies remain identical, including combat control application/rollback, runtime Load/Reset, currency editing, catalog browsing/rendering, persistent request handling and control schema/range checks. The inherited baseline checks, player-only hooks, currency/capacity writers and generation protection are preserved. Exact hashes and method comparisons are in `evidence/preservation_audit_v032.json` and `config/v031_reuse_hashes.json`.

## Actual integrated flow

1. Items / Recipes exposes **Export ALL item IDs (read-only)**, Cancel and Save JSONL in a compact row, plus progress.
2. Start requires an initialized matching protocol and loaded player. It snapshots the native generation, creates a unique app-specific output and a single writer worker.
3. Java submits only `NativeBridge.request("catalog", "@-1||OFFSET", 0, 0, false)`. Native indexing retains its existing bounded Unity callback implementation. No new hooks/getters or gameplay mutations were added.
4. The existing ModMenu poller remains the only consumer of `takeGameResults()`. Export receipts are routed by their unique request ID; catalog browsing and persistent action receipts continue through their existing paths.
5. Each receipt must match request kind, exact All Types key/offset, CATALOG state and original generation. The writer validates the four-column header, 40-row page size, stable total, expected offset, Int32 fields, exact page row count and IDs unique across all pages. There is only one pending page and no next request until the file worker acknowledges the current page.
6. The writer commits a `.partial` file only after the declared number of unique rows has been written. Success shows the actual count/path and remembers that completed export for later retrieval. It makes no invented records.
7. Save JSONL launches the system `ACTION_CREATE_DOCUMENT` picker from a small platform Fragment and copies the completed file on a worker. The user can choose Downloads or another provider, then share it with Files. No provider/Activity manifest edit, FileProvider or broad storage permission is added. Supplied OverrideActivity and UnityPlayerActivity smali do not override onActivityResult, so their inherited Activity routing can deliver Fragment results without modifying the primary DEX. This static routing observation still needs device verification.

File parsing/writing/copying occurs off the Android UI thread. The Unity callback is unchanged. Normal polling cadence remains unchanged outside an active export; active exports use the existing 100 ms receipt cadence. The native catalog cache itself remains the existing implementation.

## Read-only and lifecycle behavior

Export code never submits item, stat, capacity, currency, GM, learning or Manual-creation actions. It writes only separate JSONL output and menu preferences/diagnostics, never player save files. Persistent editors remain explicit existing actions and are not replayed by export or Load.

Cancellation, app pause/background, Activity destruction, changed/unloaded world, timeout, malformed receipts, native failures, changing totals and duplicate IDs abort the session. Cleanup is queued after in-flight IO, including cancellation racing a final rename; unpublished output is discarded. Cleanup errors are logged and shown rather than silently reported as success. Late receipts/callbacks cannot re-open a cancelled session. A stale `.partial` left by process death is removed on the next export; completed prior exports are retained.

The document picker may be cancelled without deleting the original JSONL. Fragment state handles picker results/configuration changes; the copy uses application ContentResolver rather than a retained Activity reference. A provider failure attempts to remove only the newly created incomplete destination. If the process is killed during document copying, an incomplete destination can remain; the restored UI permits retry and instructs the user to remove that destination. The completed app-specific JSONL is retained. These Android lifecycle paths are implemented and statically reviewed, not device verified.

Bounds: 100,000 unique rows; receipt <=65,536 UTF-16 chars / <=42 split lines; 40 records/page; one outstanding request; per-operation 45 s Java watchdog plus inherited native request expiry; completed-file copy <=64 MiB with a 64 KiB buffer. Raw type/level Int32 values, including unfamiliar categories or sentinel levels, are preserved; editing ranges are not imposed on read-only data.

## Schema and honest coverage

The current native transport indexes **non-hidden ConfItemProps rows**. ALL means all rows available through that existing catalog path, not all game configuration or learnable skills. Hidden item rows, independent skill/manual tables, affixes and generated Manual instances are outside this stage. The user reports about 11 current browser Manual entries; no total Manual count is independently asserted.

| JSONL field | Meaning and limitation |
|---|---|
| kind, id | Actual item record / ID from the native page |
| display_name | The displayed/sanitized native catalog name, without claiming a language |
| props_type, level | Actual raw native category and item level; **level is not rarity** |
| name_key | Visible `item_name...` unresolved key when available; otherwise null |
| name_key_provenance | `visible_unresolved_key` or null; no generated name key |
| display_name_is_localization_fallback | true for an identified visible key/#ID fallback, otherwise null because four-column transport cannot certify every displayed string |
| name_status | unresolved_fallback or display_only_localization_unverified |
| name_en, name_ch, name_tc, name_kr | null until an independent language/key collector is verified |
| rarity, grade, rarity_color, description, subtype | null; never inferred from level/name/ID |
| source_table | ConfItemProps, verified from existing catalog code |
| source, catalog_scope, collector_version | Existing v0.3.1 native transport / non-hidden scope / 0.3.2 consumer |
| snapshot_generation | Native world/save generation validated for the session |

The exact missing keys `item_name1041161` and `item_name1041162` are covered by exporter regressions and the existing native localization tests. A resolved name's original key is not present in the four-column receipt; this release cannot recover it without a future native transport extension. Returning null is intentional. The CSV builder retains displayed names without inventing English/Chinese names and keeps books, skill templates and Manual instances distinct.

## Validation performed

| Check | Result |
|---|---|
| Supplied ZIPs CRC / matching game library and metadata hashes | PASS; raw inputs excluded from publication |
| All existing host suites | PASS: core 26 cases / 94 assertions, policy 212 assertions, editor 215 checks, hotfix 32,834 checks, inherited research 10 tests |
| Current Python suite | PASS: 47 tests, including DEX-only multidex replacement/tamper/native mismatch tests |
| Original v4 Python tests | PASS: 4 tests |
| Existing actual Java UI guard | PASS: 9 checks |
| Original v4 Java writer cases | PASS: 83-row export, quoting/offset/duplicates/cleanup |
| Expanded writer/generation/copy regressions | PASS: 90 checks |
| Actual Java-generated host JSONL parsed by Python | PASS: 1,643 unique synthetic rows / 42 bounded pages, Unicode and explicit unknowns; not an Android dump |
| Java ECJ / D8 compilation | PASS: 86,436-byte DEX 035, 70 helper classes, exporter entry points present |
| New DEX SHA-1/Adler32/header and unchanged JNI descriptors | PASS: all 19 match both actual v0.3.1 DEX and reused SO |
| Reused ARM64 ELF/dependencies/alignment | PASS: ET_DYN AArch64, 16 KiB LOAD alignment, RELRO, non-executable stack, system dependencies only |
| DEX-only patch CRC / internal SHA-256 checksums | PASS |
| Real APK rebuild/sign/install/startup | NOT PERFORMED; helper patch only |
| Android exporter functional/save/retrieval/long-session test | NOT DEVICE VERIFIED |

Compiler: OpenJDK 17.0.20, pinned ECJ 3.38.0 and D8/R8 8.7.18, official Android 35 platform jar, min API 23 retained. Native NDK compilation was intentionally unnecessary. Logs, build identity, SDK source and machine-readable reports are in `evidence/`. Existing v0.3.1 evidence retains its original versioned filenames; this table references new v0.3.2 reports/logs.

## Status and remaining work

| Feature | Source | Host/static | Compiled | Device |
|---|---|---|---|---|
| Paged read-only export / count/path | IMPLEMENTED | PASS | YES | NOT VERIFIED |
| Cancellation/generation/duplicate/partial cleanup | IMPLEMENTED | PASS | YES | NOT VERIFIED |
| System Save JSONL / copy and recovery | IMPLEMENTED | Copy/route checks PASS | YES | NOT VERIFIED |
| Combat/EXP/stat/currency/capacity/browser | PRESERVED | Source/native parity PASS | Native reused | v0.3.1 user report; v0.3.2 regression check pending |
| Complete localization/rarity/descriptions | NOT IMPLEMENTED in collector | Roadmap only | NO | NOT VERIFIED |
| Complete skill/manual catalog / safe instance reading | MAPPED ONLY | Roadmap only | NO | NOT VERIFIED |

No known failed host tests remain. Outstanding risks are device-specific Fragment/document-provider routing, background/process-death behavior and natural generation changes interrupting an export. Run the export after loading a save, preferably idle on the world map without changing scenes. No device JSONL or file count is fabricated. Next: install this DEX over working v0.3.1, run `TEST_CHECKLIST.txt`, send the actual JSONL, then measure gaps before implementing the bounded collector in `docs/CATALOG_COLLECTOR_NEXT.md`. NPC editing and speculative Manual creation remain excluded.

Installation, correct multidex slot, signing and rollback are in `README_ID.txt`. v0.3.1 stays untouched in its separate repository directory. Public download/source verification is recorded after publication.

Android API references consulted: [Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files), [platform Fragment](https://developer.android.com/reference/android/app/Fragment), [Activity lifecycle callbacks](https://developer.android.com/reference/android/app/Application.ActivityLifecycleCallbacks).
