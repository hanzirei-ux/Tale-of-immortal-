# Build v0.3.2 — DEX-only catalog exporter

Continue v0.3.1 commit `069f30c01227dd2ecdc5fab63bfafb17243bf1c2`. Native gameplay code/JNI declarations are unchanged. No NDK or new native hooks are needed for this release. Keep the installed v0.3.1 `libtoimodmenu.so`, SHA-256 `ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729` (711,848 bytes, protocol 4).

Requirements: Java 17, Python 3, g++ for inherited host suites, Android SDK platform 35 `android.jar`, pinned ECJ/D8 tools. Use the official SDK Manager to install `platforms;android-35`. Pinned tool downloads are public compiler dependencies, not game files.

```bash
python3 tools/fetch_java_tools.py /tmp/toi-java-tools
bash scripts/test_host.sh
python3 tools/test_java_ui_state.py --java-tools /tmp/toi-java-tools
python3 tools/test_catalog_exporter.py --java-tools /tmp/toi-java-tools
python3 -m unittest discover -s reference_exporter_v4/tests -p 'test_*.py' -v
python3 tools/build_menu_dex_only.py --java-tools /tmp/toi-java-tools --android-jar /path/to/android-35/android.jar
```

For component verification, extract **only this project's own native helper** from the preserved v0.3.1 patch to `patch/lib/arm64-v8a/libtoimodmenu.so`. Install `requirements-analysis.txt` dependencies for ELF parsing; no game APK/assets/metadata are necessary.

```bash
python3 tools/verify_v032_components.py
python3 tools/build_v032_package.py
```

The packager validates the current source revision, new DEX fingerprint, exact native reuse fingerprint, and all 19 unchanged JNI descriptors. The resulting ZIP contains one APK replacement, `APK_ROOT/classes2.dex`. It intentionally contains no SO. The DEX build record identifies v0.3.2 source; the reused SO retains its original v0.3.1 build provenance. A shared new native/Java revision is not claimed.

For private local APK repacking, optionally use `tools/apply_catalog_export_patch.py input-v031.apk exporter-patch.zip output-unsigned.apk`. It recognizes the exact v0.3.1 helper/native pair, replaces the helper's existing multidex slot, keeps game/native payloads, strips old ZIP signing entries and checks alignment. Sign the output separately with the installed app's key. This optional path is host tested with synthetic ZIPs; no real APK was built/signed/installed in this milestone. Older pair-replacement tools are historical and do not accept this DEX-only patch.

`reference_exporter_v4/` preserves the entire supplied source package. Its original integrator was applied to v0.3.1 once, then the inserted lifecycle/IO/routing code was hardened in place. Do not run that old integrator over an already integrated ModMenu. Its original tests remain available; the expanded tests exercise the final writer and transport guard.
