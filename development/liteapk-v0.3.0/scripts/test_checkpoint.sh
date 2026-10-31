#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
task_build=${TOI_CHECKPOINT_BUILD_DIR:-/tmp/toi-v03-editor-tests}
mkdir -p "$task_build"
"${CXX:-g++}" -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror -pthread \
  -I"$task_root/overlay/native" "$task_root/tests/editor_tests.cpp" \
  "$task_root/overlay/native/managed_access.cpp" "$task_root/overlay/native/game_editors.cpp" \
  -o "$task_build/editor_tests"
"$task_build/editor_tests"
