# Tale of Immortal v0.3.6 — DEX-first Full Catalog schema

**SOURCE IMPLEMENTED / HOST TESTED / COMPILED — NOT DEVICE VERIFIED.** A real replacement helper DEX and DEX-only patch have been built. **The requested full native table collector is PARTIALLY IMPLEMENTED / BLOCKED_NATIVE.** No new native reader/SO is included. The new button exports all data reachable through JNI4 and truthful metadata schemas, not unexposed Realm/rarity/skill values.

## Artifacts and compatibility

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `TaleOfImmortal_ModMenu_v0.3.6_FullCatalog_DEXOnly_BinaryPatch.zip` | 68221 | `75d988db79166ba07a0b3aa5499931d25e6f4866689e1566acef4a72e88acfae` |
| New replacement classes2.dex | 137072 | `d79db2a4171dcf268a85e0289ddb224577325366ccdfd5355e5134b323c7dbe3` |
| Required existing v0.3.1 SO, reused by v0.3.2; excluded from patch | 711848 | `ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729` |

Compile-source revision: `7a4b0b54640955f72fea4364657033f9b78f75eea763f870b567117c78814573`. JNI remains protocol 4 with 19 matching native declarations; the proven ARM64 SO retains its old build provenance. No newly compiled native pair is claimed. DEX is version 035, min API 23, compiled with OpenJDK 17.0.20, pinned ECJ 3.38.0 / D8 8.7.18 and official Android 35 SDK jar. Android 11 ARM64 and Xiaomi 11T Android 14 remain compatibility targets; v0.3.6 is not device tested.

The ZIP contains only APK_ROOT/classes2.dex, README_ID.txt, CHANGELOG.txt, TEST_CHECKLIST.txt, COLLECTOR_LIMITS.txt, THIRD_PARTY_NOTICES.txt and SHA256SUMS.txt. There is no complete APK, new SO, original primary DEX or game asset. No APK was requested, built, signed or installed. The optional local replacement utility was tested only with synthetic ZIP fixtures.

## Existing project and accessible research

Source continues GitHub v0.3.2 commit `7d64bcfde08051b97b1f150ba88cefb244b5d59e`. Its actual supplied binary patch was checked against ZIP SHA-256 `069fa832cf0db3164bf32135f21cd4faafe2e9ad0dd6d73d471ebb9ccb4717ca` and helper DEX `7e1f65e069785ab12ed89479c7e74cff6ad8fbcdc21351622354dea6b67a9ac9`. All compiled-source files matched the pinned repository before modification. An older local post-publication evidence file differed, not gameplay/compiler source; its historical status is not used as new evidence.

The v0.3.4 CollectorPrep and v0.3.5 Binary UI Validation ZIPs were not in current attachments, repo, or exact/short filename search results. No inspection of those packages or unpublished v0.3.3–v0.3.5 implementation is claimed. Work reuses accessible v0.3.2/v4 code, the v31 metadata parser, registration audit, ManagedAccess/JNI mappings, current UI and build tooling.

The supplied tales.zip has 9,006 entries and CRC PASS. Its libil2cpp.so is 144,951,312 bytes / c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099; metadata is 42,923,616 bytes / 9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3 (version 31). They match the LiteAPK profile, not old V60 patched binaries. Their contents were not modified or published. UI bundles and additional bundle ZIP were inventoried/hashed with private raw files excluded; their visual metadata is not treated as runtime configuration or a rarity rule. Save/world cache files were not used.

## Actual device dump findings

The attached v0.3.2 JSONL has SHA-256 `c0dfdc8a810cf7e58c0bc3da9f87e6b2fb5aad64ff877411eb56ed8855fb4f7a`, 1,835,160 bytes, **3,284 records / 3,284 unique IDs**, snapshot generation 2 and 60 visible unresolved-name fallbacks. It is genuine supplied device output from the older collector; it does not verify this new build.

| Raw ConfItemProps type | Item count |
|---|---:|
| 1 | 1357 |
| 2 | 11 |
| 3 | 395 |
| 5 | 521 |
| 6 | 856 |
| 7 | 140 |
| 8 | 4 |

Levels range from 1 to 6; no item Realm/grade/rarity is derived from those numbers or displayed text. The 11 type-2 inventory rows do not represent the full Manual or Skill database. Types 7/8 remain 144 actual items without invented labels.

Matching metadata contains PropsType constants Money=0, Pill=1, Martial=2, Equip=3, Material=5, Other=6. These are exported in their own metadata namespace. A numerical match is not enough to prove an official ConfItemType/ConfItemProps join. PropsData.get_propsType returns the distinct enum PropsDataType; that signature is not evidence for the missing relationship. No per-item official type label is supplied until actual configuration rows establish it.

## New working-source path

Items / Recipes preserves the old Export ALL item IDs operation and adds **Export Full Catalog**. The new mode uses the exact existing request `NativeBridge.request("catalog", "@-1||OFFSET", 0, 0, false)` and the existing single receipt consumer. No generic native read, unsafe manual creation, GM mutation or new hook is inserted.

ReadOnlyCatalogExport's verified validation/serialization path is reused. Small protected serialization/commit hooks allow FullCatalogExport to add versioned records without replacing the pager. The default legacy output remains byte-identical to v0.3.2 in a host comparison against the actual old Java source. Existing generation/request-ID/key/state guards, one-page-at-a-time dispatch, worker IO, cancellation, watchdog and partial-file cleanup are retained.

The new mode adds:

- Percentage/current-table/item-count/record-count progress and a permanent native-limit warning.
- A begin/complete manifest, metadata facts and per-field provenance for actual item rows.
- 3,284-ID reference protection. If any reference ID is missing, full-schema commit fails with REFERENCE_ID_GAP; it does not invent replacement rows. The legacy exporter remains available for inspecting a changed catalog.
- Metadata enum definitions and **14 global Assembly-CSharp schema contracts**. The global MartialInfoData is type index 7962; a different nested type with the same short name is deliberately excluded.
- Observed raw type IDs/counts in a separate ConfItemProps.type namespace. Metadata enums do not silently become item labels.
- COMPLETE_SUPPORTED_SCOPE with all_native_tables_collected=false. This is completion of supported pages, not completion of unexposed tables.
- The same Android Save JSONL workflow and last-completed-file retrieval, with separate item/full filenames. No new manifest entry or storage permission is needed by the implementation.

Native/GameEditors still indexes only non-hidden items. Hidden=0 is marked VERIFIED_JOIN because the validated existing native filter excludes hide != 0; no new direct field read is claimed. Source table/namespace also come from that verified dispatch/filter relationship. Visible item_name... fallback keys are INFERRED because the raw name/key field is not included in the four-column receipt. Separate language strings are unknown even if display text looks English.

## Evidence model and output

Game fields use exactly VERIFIED_RUNTIME, VERIFIED_METADATA, VERIFIED_JOIN, INFERRED or UNKNOWN. These labels record the stated source/evidence, not an automatic Android certification. Host-generated fixtures or replay do not certify a newly executed device collector.

| Data | Current evidence/capability |
|---|---|
| Item ID, display name, raw type, level | Existing runtime receipt; VERIFIED_RUNTIME |
| Non-hidden membership/source binding | Verified existing filter/dispatch; VERIFIED_JOIN |
| Visible fallback key/status | Pattern from displayed fallback; INFERRED |
| PropsType enum and global field definitions | Matching metadata; VERIFIED_METADATA |
| Original internal name/key, EN/CN strings, description, subtype/className | Not transported; UNKNOWN |
| Configured Realm names/phase/quality, item Realm requirements | Not transported / item join unverified; UNKNOWN/BLOCKED_NATIVE |
| Item Grade/Rarity/color and their mapping | Not transported / semantics unverified; UNKNOWN/BLOCKED_NATIVE |
| Books, skill/manual templates, affixes, live generated Manual instances | No table/instance reader in JNI4; BLOCKED_NATIVE |

Full JSONL contains item, item_type, metadata_contract and catalog_manifest records. The parser splits independent files for Items, Item Types, Realms, Grades, Rarity, Localization, Books, Skill Templates, Manual Templates, Manual Instances and metadata schemas, plus manifest/items.csv. Unsupported data sections stay empty with BLOCKED_NATIVE. Metadata schema rows are not counted as Realm/Manual data rows.

The machine schema is `schema/full_catalog_v036.schema.json`. Filter dimensions remain independent: **realm_id | props_type | subtype | grade | rarity | level**, with individual status columns. Cultivation quality is separate again. No grade/color/Realm/name is manufactured from item level, ID or display-name spelling.

`tools/normalize_full_catalog.py` accepts legacy or full-schema data and optional baseline files. It preserves source namespaces, all reference IDs, known values when new fields are UNKNOWN, and a bounded observation history. Verified conflicts fail instead of silently overwriting. Duplicate IDs within one input, invalid status/value combinations, mixed generations, malformed manifests/JSONL and count mismatches fail before an output directory is committed. Existing output is never overwritten. CSV text is formula-guarded without altering original JSONL values.

## Preservation and runtime safety

All 26 native source files plus NativeBridge.java remain byte-identical to the stable baseline; SO bytes are identical. Twenty-two existing UI method bodies remain unchanged, including combat application/rollback, Load/Reset, player request routing, currency editor and catalog browsing/rendering. Control IDs/ranges, 19 JNI signatures, player-only checks, multiplier semantics and capacity/currency safeguards are unchanged.

The new FullCatalogExport is a Java consumer/serializer. It calls no native API itself, owns no IL2CPP object and never invokes AddItem, RewardProp, stat/currency/capacity changes, skill learning or save writes. The UI only queues read-only catalog requests. World/save changes, pause/close, timeout, failure and cancellation retain old guards; cleanup runs after in-flight worker operations, including a final-rename race. Completed previous exports remain usable when a new session fails.

Output bounds remain 100,000 item IDs, 40 rows per page, 65,536-character page receipts, one pending request and 45-second Java operation watchdog plus existing native expiry. Full schema writes stream to app-specific storage; no whole-catalog enumeration is added to Unity's main thread. Save copy remains bounded at 64 MiB. Host replay full JSONL was 6,256,819 bytes, within that limit. No phone ANR or session-stability result is claimed.

## Tests and actual binary validation

| Verification | Result |
|---|---|
| Existing core/policy/catalog tests | PASS: 26 core cases / 94 assertions, 212 policy assertions, catalog guards |
| Native editor/hotfix suites | PASS: 215 editor checks / 32,834 hotfix checks |
| Inherited research tests | PASS: 10 |
| Current Python suite | PASS: 80 tests |
| Existing Java exporter/copy/guard tests | PASS: 90 expanded checks plus original 83-row writer cases |
| Existing actual Java UI state guard | PASS: 9 checks |
| New full-schema Java writer | PASS: 30 checks |
| Byte parity of default writer against actual v0.3.2 source | PASS |
| Real old phone dump replay through new Java writer | PASS: 3,284 original IDs/name/type/level preserved, 3,313 full-schema records |
| Full/legacy merge and all reference IDs | PASS: 3,284 retained; no fabricated Realm/Manual rows |
| Draft 2020-12 JSON Schema over replay | PASS |
| Static schemas/enum/defaults/registration | PASS: 14 global schemas, 6 enum constants; 30 method identities mapped separately |
| Existing native method specs/currency constants | PASS: 28 signatures, 4 currency IDs, matching hashes/native exports |
| Actual DEX header, SHA-1, Adler32, compiled classes/entry points | PASS |
| JNI against actual v0.3.2 DEX and reused SO | PASS: 19 descriptors / protocol 4 |
| ARM64 ELF/dependencies/alignment | PASS: reused ET_DYN AArch64, 16 KiB LOAD alignment, RELRO, non-executable stack, system dependencies |
| Patch ZIP CRC/internal checksums | PASS |
| Full APK build/sign/install | NOT PERFORMED / NOT REQUESTED |
| New v0.3.6 phone execution/save/load/stability | NOT DEVICE VERIFIED |

Build/test records and logs are in evidence/. The phone-replay output itself and raw user dump are private intermediates, not public release data. Published reference configuration contains IDs/counts/hashes only, not item-name assets or saves. No failed host tests remain.

## Exact blocker / next step

`docs/NATIVE_COLLECTOR_BLOCKER_V036.md` and `config/native_collector_requirements_v036.json` identify the unexposed cached fields and 30 metadata getter/list/instance methods. Method indices/tokens are references, never runtime addresses. Runtime calls for these new tables are not validated and no new native collector binary is included.

The smallest future extension is a separately versioned, read-only table/page RPC dispatched by the current verified Unity callback and ManagedAccess, with its own explicit capability, generation, byte/row bounds and managed-object lifetime checks. It must leave legacy catalog/Add Item and all gameplay hooks alone. It is needed for the actual table values and verified joins; DEX alone cannot produce those data through the existing boundary. Manual instances need a separate verified player-owned object traversal, not unsafe creation. A full APK is not needed for that work.

Deliverable status: **DEX-only supported collector upgrade COMPILED; full native data collection remains PARTIALLY IMPLEMENTED/BLOCKED_NATIVE.** Install per README_ID.txt, check the old gameplay features and both export buttons, then validate the actual new phone JSONL using TEST_CHECKLIST.txt. v0.3.1/v0.3.2 rollback files remain intact in GitHub. Public download/source checks are recorded after publication.
