# Build v0.3.1 helper components

Requirements: Java 17, Python 3, g++, CMake >=3.22, NDK r27c (27.2.12479018), Android platform 35 android.jar. Dobby is the existing vendored revision; retain its local fixes and notices.

```bash
python3 tools/fetch_java_tools.py /tmp/toi-java-tools
bash scripts/test_host.sh
python3 tools/test_java_ui_state.py --java-tools /tmp/toi-java-tools
export ANDROID_NDK_ROOT=/path/to/android-ndk-r27c
bash scripts/build_android.sh
python3 tools/build_menu_dex_only.py --java-tools /tmp/toi-java-tools --android-jar /path/to/android-35/android.jar
python3 tools/verify_v031_components.py
python3 tools/build_v031_package.py
```

Install Python dependencies from requirements-analysis.txt for ELF verification. Native and DEX builds each write a record with the same compile-source content revision. The packager rejects stale/mismatched artifacts or old v0.3 hashes. This is reproducible source/build configuration; byte-for-byte results across other compiler dates/environments are not promised.

Private baseline audits, when the supplied files are available:

```bash
python3 tools/verify_editor_targets.py /private/libil2cpp.so /private/global-metadata.dat --report evidence/editor_target_verification_v031.json
python3 tools/audit_hotfix_preservation.py --v02 /private/v02-source --v030 /private/v030-source --report evidence/preservation_audit_v031.json
```

`verify_artifacts.py` can additionally compare the retained original/primary DEX and game prologues using private inputs. No game files are downloaded by the build. No APK is signed or installed by these steps. For optional local APK replacement, `apply_hotfix_to_apk.py` accepts recognized v0.2/v0.3 pairs and preserves the helper's actual multidex slot; its output needs signing with the installed app's key.
