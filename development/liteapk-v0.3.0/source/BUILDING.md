# Rebuild v0.2.0-test

The included binaries were built successfully on Linux x86_64 using Android NDK r27c / Clang 18, CMake 3.31.6, Make, Java 17, Eclipse ECJ 3.38.0, Android SDK 35 `android.jar`, R8/D8 8.7.18, and smali/baksmali 2.5.2. The native target is ARM64, API 23, Release, static libc++ and static Dobby. This is reproducible as a build procedure; byte-for-byte identity across paths, dates, compilers and debug information is not promised.

From this project directory, with those tools installed:

```bash
export ANDROID_NDK_ROOT=/absolute/path/android-ndk-r27c
bash scripts/build_android.sh
python3 tools/fetch_java_tools.py /absolute/path/toi-java-tools
python3 tools/build_dex.py /absolute/path/original-classes.dex --java-tools /absolute/path/toi-java-tools --android-jar /absolute/path/android-sdk/platforms/android-35/android.jar
python3 tools/refresh_patch_manifest.py
python3 -m pip install -r requirements-analysis.txt
python3 tools/verify_artifacts.py --original-dex /absolute/path/original-classes.dex --game-lib /absolute/path/original-libil2cpp.so --report evidence/rebuilt-artifacts.json
bash scripts/test_host.sh
```

The DEX builder verifies the original DEX, all compiler JAR fingerprints, and both the original and patched Activity disassembly hashes. It disassembles the actual DEX, applies only the lifecycle additions, reassembles the primary DEX, compiles the Java source and emits a separate helper DEX. It does not use extracted save/cache folders. The native build uses the vendored Dobby commit and local fixes; no external Dobby checkout is needed.

The provided Android Gradle library project is an alternative source integration path; its AAR task was not run in this environment. The direct NDK/ECJ/D8/smali procedure above was actually run. Neither path supplies the missing game APK manifest, resources or assets.

To reproduce the hook profile, install Il2CppDumper 6.7.46 and dump the exact baseline library/metadata to obtain `script.json`. Then use:

```bash
python3 tools/generate_hook_profile.py /absolute/path/original-libil2cpp.so /absolute/path/script.json native/baseline_profile.hpp
```

The existing checked-in profile is already resolved against this exact library; normal builds do not need to run the dumper again. Metadata indices are never used as code addresses. `native/baseline_profile.json` contains signatures, RVAs, file offsets and prologue bytes. ASLR load base is resolved at runtime.

Keep game files and patched game DEX outside public source repositories. If publishing original development source, omit `patch/classes.dex`, supplied APKs, extracted assets/metadata/libraries, saves and caches. Review historical/reference material before publication as well.
