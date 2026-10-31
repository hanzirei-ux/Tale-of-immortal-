#!/usr/bin/env bash
set -euo pipefail
toi_project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
toi_build_dir="${TOI_BUILD_DIR:-$toi_project_root/build-host}"
mkdir -p "$toi_build_dir"
cd "$toi_project_root"
${CXX:-g++} -std=c++17 -Wall -Wextra -Wpedantic -Werror -pthread -I native \
  native/bridge.cpp native/sha256.cpp native/il2cpp_backend.cpp tests/native_tests.cpp \
  -ldl -o "$toi_build_dir/toi_core_tests"
"$toi_build_dir/toi_core_tests"
${CXX:-g++} -std=c++17 -Wall -Wextra -Wpedantic -Werror -pthread -I native \
  native/modifiers.cpp native/mod_api.cpp tests/policy_tests.cpp -ldl \
  -o "$toi_build_dir/toi_policy_tests"
"$toi_build_dir/toi_policy_tests"
${CXX:-g++} -std=c++17 -Wall -Wextra -Wpedantic -Werror -I native tests/catalog_tests.cpp -o "$toi_build_dir/catalog_tests"
"$toi_build_dir/catalog_tests"
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s reference_research_v1/tests -p 'test_*.py' -v

${CXX:-g++} -std=c++17 -Wall -Wextra -Wpedantic -Werror -pthread -I native \
  native/managed_access.cpp native/game_editors.cpp tests/editor_tests.cpp -o "$toi_build_dir/toi_editor_tests"
"$toi_build_dir/toi_editor_tests"
