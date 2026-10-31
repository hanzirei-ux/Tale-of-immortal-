#!/usr/bin/env python3
"""Record newly built component hashes; baseline guards are never auto-relaxed."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    baseline = json.loads((ROOT / "config/baseline.json").read_text())
    files = {}
    for name in ("classes.dex", "toimodmenu.dex", "lib/arm64-v8a/libtoimodmenu.so"):
        path = ROOT / "patch" / name
        files[name] = {"size": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest = {"version": "0.2.0-test", "abi": "arm64-v8a", "min_api": 23, "device_tested": False,
                "signed_apk_produced": False, "files": files,
                "metadata_sha256": baseline["global-metadata.dat"]["sha256"],
                "baseline_apk_entries": {"classes.dex": baseline["classes.dex"]["sha256"],
                    "lib/arm64-v8a/libil2cpp.so": baseline["libil2cpp.so"]["sha256"],
                    "lib/arm64-v8a/libandroidoyunclub.so": baseline["startup_library_verified_this_milestone"]["sha256"]}}
    (ROOT / "patch/patch_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Updated exact-baseline patch manifest")
