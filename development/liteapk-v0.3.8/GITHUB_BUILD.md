# Tale of Immortal Android — v0.3.8 NPC + Sect GitHub build

**STATUS (2026-11-07): CI configuration only. No new Android .so/.dex was built or tested.**

This separate branch preserves main and the existing v0.3.7 Item Manager.
The build is intentionally blocked until a complete matching source bundle is available.
The bundle was prepared from:
- v0.3.7 Item Manager test-build ZIP's `source_changes/` (NOT the old v0.3.6 sources alone).
- v0.3.8 NPC/Sect source-only ZIP's `overlay/`, `apply_to_v037.py`, `v037_source_hashes.json`, and `tests/`.

Expected bundle name: `TOI_v038_GitHub_SourceBundle_PRIVATE.zip`
Expected SHA256: `8a84869f1687700009544ac412f3901c42be9d3792de1ad39284ae73ee0b4235`

## Source confidentiality
The bundle contains generated Item Manager catalog source derived from the user's game.
**Do not upload this private bundle to the public repository/branch.**
Instead place the bundle at a temporary private HTTPS download location and configure
the Actions secret `TOI_V038_SOURCE_BUNDLE_URL` to that link.
Avoid printing the URL, and expire/delete the private URL after building.

## How to run
1. Make the matching ZIP available via the Actions secret URL above.
2. Push a change to `development/liteapk-v0.3.8/build_inputs/run.flag` on this
   branch to trigger `.github/workflows/toi-v038-npc-sect.yml`, or dispatch the
   workflow from GitHub Actions after it exists on the default branch.
3. The job verifies SHA256, restores v0.3.7 sources over the existing v0.3.6 tree,
   applies v0.3.8 only after checking original source hashes, uses NDK r27c /
   Android SDK 35 / pinned ECJ and D8, builds BOTH outputs, and uploads a single
   patch ZIP artifact.
4. Download the artifact only after the run is green, read its manifest, and test
   on a backup save first. Do not overwrite a working APK without testing.

## Feature scope and limits
- Planned: NPC list, stat editor, one-step Realm attempt, NPC cultivation bonus
  only for members of the player's exact Sect.
- Not implemented: NPC monthly AI acceleration, automatic breakthrough materials,
  manual/book quality, studying/training books, story/relationship changes.
- Static CI success is not Android runtime validation; do not mark features stable.
- No original APK, game libil2cpp, metadata, or saves are uploaded by this workflow.
- The installed v0.3.7 source is never replaced by the older v0.3.6 file as the
  starting point for the v0.3.8 feature changes.

## Recovery
If the GitHub build fails, examine the exact failing step and retain the existing
working v0.3.7 classes2.dex + libtoimodmenu.so pair. Both binaries must always be
replaced together, not separately.
