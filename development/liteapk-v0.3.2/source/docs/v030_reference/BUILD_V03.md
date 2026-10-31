# Rebuild the v0.3 components

Use this existing project. Required tools are Java 17, CMake >=3.22, NDK r27c (27.2.12479018), Python 3 and Android platform 35 android.jar. Dobby and its pinned local fixes are vendored.

```bash
python3 tools/fetch_java_tools.py /tmp/toi-java-tools
bash scripts/test_host.sh
export ANDROID_NDK_ROOT=/path/to/android-ndk-r27c
bash scripts/build_android.sh
python3 tools/build_menu_dex_only.py --java-tools /tmp/toi-java-tools --android-jar /path/to/android-35/android.jar
python3 tools/verify_v03_components.py
python3 tools/build_v03_package.py
```

The helper DEX is `out/toimodmenu.dex`, packaged as `APK_ROOT/classes2.dex`. The SO is `patch/lib/arm64-v8a/libtoimodmenu.so`. Do not rebuild the primary game DEX or replace libil2cpp.so. Install both new components together.

`verify_v03_components.py` checks the freshly built pair without needing proprietary inputs. The committed `evidence/editor_target_verification.json` records the baseline target audit; rerun it with the privately supplied matching library and metadata for independent target verification:

```bash
python3 tools/verify_editor_targets.py /private/libil2cpp.so /private/global-metadata.dat --report evidence/editor_target_verification.json
```

`tools/verify_artifacts.py` additionally compares the retained primary v0.2 DEX and original native registrations when private reference files are available. No game input is downloaded by the build or required to compile the original mod source. A compile/static pass is not device verification. APK repacking and signing use the user's existing v0.2 APK and key.
