#!/usr/bin/env bash
set -euo pipefail
toi_project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
toi_source_revision=$(python3 "$toi_project_root/tools/source_revision.py")
toi_ndk_root="${ANDROID_NDK_ROOT:-${ANDROID_NDK_HOME:-}}"
if [[ ! -f "$toi_ndk_root/build/cmake/android.toolchain.cmake" ]]; then
  echo 'Set ANDROID_NDK_ROOT to NDK r27c (27.2.12479018).' >&2
  exit 2
fi
toi_build_dir="${TOI_ANDROID_BUILD_DIR:-$toi_project_root/build-android}"
cmake -S "$toi_project_root" -B "$toi_build_dir" -G 'Unix Makefiles' \
  -DCMAKE_TOOLCHAIN_FILE="$toi_ndk_root/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-23 -DANDROID_STL=c++_static \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "$toi_build_dir" --target toimodmenu -j "${TOI_BUILD_JOBS:-4}"
mkdir -p "$toi_project_root/patch/lib/arm64-v8a"
cp "$toi_build_dir/libtoimodmenu.so" "$toi_project_root/patch/lib/arm64-v8a/libtoimodmenu.so"
"$toi_ndk_root/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" --strip-unneeded \
  "$toi_project_root/patch/lib/arm64-v8a/libtoimodmenu.so"
if [[ "$(python3 "$toi_project_root/tools/source_revision.py")" != "$toi_source_revision" ]]; then
  echo 'Source changed during native build; rebuild both components.' >&2; exit 3
fi
python3 "$toi_project_root/tools/source_revision.py" --record native \
  --artifact "$toi_project_root/patch/lib/arm64-v8a/libtoimodmenu.so" --output "$toi_project_root/out/native_build_v031.json"
echo 'Built v0.3.1 ARM64 component; build and verify the matching helper DEX.' 
