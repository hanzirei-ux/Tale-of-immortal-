#!/usr/bin/env python3
"""Fetch pinned public compiler/DEX tools, never game files."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((Path(__file__).resolve().parents[1] / "config/java_build_tools.json").read_text())
    for entry in manifest:
        target = args.destination / entry["name"]
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == entry["sha256"]:
            print("Already verified:", target.name)
            continue
        with urllib.request.urlopen(entry["url"], timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Download fingerprint mismatch: " + target.name)
        target.write_bytes(data)
        print("Verified:", target.name)
