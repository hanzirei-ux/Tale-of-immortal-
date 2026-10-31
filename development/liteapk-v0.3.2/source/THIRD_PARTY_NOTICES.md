# Third-party materials

Dobby is vendored under `third_party/Dobby`, pinned to commit `9c85e74f92eda36b99ddb0fddb17a9df2278a4d3`. Its Apache 2.0 license is included there. `LOCAL_FIXES.patch` records this project's changes. Dobby includes additional source under its `external` directory; retain all bundled notices when redistributing original development source.

The compiled component statically links the Android NDK C++ runtime. Relevant runtime notices are in `third_party/NDK_RUNTIME_NOTICE.txt`.

Java/DEX/compiler tools are not bundled; the fetch manifest pins their official Google/Maven URLs and SHA-256 fingerprints. Consult their distributions for their licenses. The optional Android Gradle path is source only.

`patch/classes.dex` is a privately transformed derivative of the user-supplied third-party game package. It is not original mod source and is not licensed for public redistribution by this project. Do not include it, game APKs/libraries/metadata/assets, or private saves/caches in a public source repository.
