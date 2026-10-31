# Build v0.3.6 — DEX-only full schema

Java 17, Python 3, pinned ECJ 3.38.0 / D8 8.7.18 and official Android 35 android.jar are reused. D8 min API remains 23. No NDK build is required. Keep the exact v0.3.1 native SO already used by v0.3.2.

```bash
python3 -m pip install -r requirements-analysis.txt -r requirements-catalog-test.txt
python3 tools/fetch_java_tools.py /tmp/toi-java-tools
python3 tools/generate_catalog_definitions.py
bash scripts/test_host.sh
python3 tools/test_java_ui_state.py --java-tools /tmp/toi-java-tools
python3 tools/test_catalog_exporter.py --java-tools /tmp/toi-java-tools
python3 tools/test_full_catalog.py --java-tools /tmp/toi-java-tools
python3 tools/build_menu_dex_only.py --java-tools /tmp/toi-java-tools --android-jar /path/to/android-35/android.jar
```

The checked metadata schemas and 3,284 reference IDs are project configuration, generated Java is deterministic, and no private game input is needed for the regular DEX build. The reference config embeds no displayed names/assets/saves. The pinned schemas and IDs do not grant Java a new native read capability.

For ABI/component verification, extract this project's own v0.3.1 SO into patch/lib/arm64-v8a/libtoimodmenu.so, and its own v0.3.2 classes2.dex to a private reference path. Both are available from prior preserved helper ZIPs, not the original game APK.

```bash
python3 tools/verify_v036_components.py --v032-dex /private/v032-classes2.dex
python3 tools/build_v036_package.py
```

The packager requires the current source revision, actual new DEX hash, native fingerprint ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729, protocol 4 and all 19 matching JNI declarations. It rejects old renamed DEX files and excludes SO/game files. No full APK is built or signed.

Optional private audits, only with the already supplied extraction:

```bash
python3 tools/build_catalog_metadata_v036.py /private/libil2cpp.so /private/global-metadata.dat
python3 tools/generate_catalog_definitions.py
python3 tools/verify_editor_targets.py /private/libil2cpp.so /private/global-metadata.dat --report evidence/editor_target_verification_v036.json
python3 tools/test_full_catalog.py --java-tools /tmp/toi-java-tools --baseline-source /private/v032-source --device-dump /private/original-phone.jsonl --report evidence/full_catalog_host_replay_v036.json
```

These reuse the v31 parser and existing registration audit, require exact hashes and never treat a MethodDef token as an executable address. No private raw inputs/dumps are copied into release packages. Host replay is explicitly not a v0.3.6 device test.

Normalize actual exports without installing any game software:

```bash
python3 tools/normalize_full_catalog.py /private/full.jsonl /private/catalog-output --baseline /private/original-v032.jsonl
```

Output is a new directory with independent JSONL sections, manifest and item CSV. Existing output folders are not overwritten, reference ID gaps fail, UNKNOWN cannot erase confirmed fields, and conflicting verified values stop the merge. JSON Schema describes the normalized/full record shape; raw v0.3.2 data goes through the legacy adapter first. No Realm/grade/rarity or language is inferred from display text.

`tools/apply_full_catalog_patch.py` is an optional local repacker for an already-owned recognized v0.3.2 APK. It replaces only the existing helper's actual multidex slot and preserves native/primary/game payloads; its output would need the user's existing signing key. It was tested only on synthetic ZIP fixtures here. The user can instead use Apktool M per README_ID.txt; no APK is requested by this project.
