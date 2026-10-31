#!/usr/bin/env python3
"""Read-only inventory; optional selective extraction excludes saves/caches.

Never overwrites an existing extracted file. Never executes native code.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

EXPECTED = {
    "libil2cpp.so": (144951312, "c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099"),
    "global-metadata.dat": (42923616, "9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3"),
}
NEEDED = {"libil2cpp.so", "global-metadata.dat", "libunity.so", "libmain.so",
          "libandroidoyunclub.so", "libcheckupdate.so", "AndroidManifest.xml", "resources.arsc"}

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_member(name):
    p = PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts and "\\" not in name

def private_member(name):
    return any(re.fullmatch(r"(save\w*|cache\w*|shared_prefs|databases)", part, re.I)
               for part in PurePosixPath(name).parts)

def inspect(path, extract=None):
    path = Path(path)
    if not path.is_file():
        return {"name": path.name, "status": "MISSING"}
    result = {"name": path.name, "size": path.stat().st_size, "sha256": digest(path)}
    if path.name in EXPECTED:
        result["expected_baseline_match"] = (result["size"], result["sha256"]) == EXPECTED[path.name]
    if not zipfile.is_zipfile(path):
        return result
    with zipfile.ZipFile(path) as z:
        entries = z.infolist()
        if sum(i.file_size for i in entries) > 4 * 1024**3:
            raise ValueError("Archive exceeds 4 GiB inspection limit")
        unsafe = [i.filename for i in entries if not safe_member(i.filename)]
        if unsafe:
            raise ValueError("Unsafe archive member path")
        result.update(zip_entries=len(entries), crc_failure=z.testzip(), selected_components=[],
                      private_entries_skipped=sum(private_member(i.filename) for i in entries))
        for index, info in enumerate(entries):
            name = PurePosixPath(info.filename).name
            if info.is_dir() or private_member(info.filename):
                continue
            if name not in NEEDED and not re.fullmatch(r"classes\d*\.dex", name):
                continue
            if info.file_size > 512 * 1024**2:
                raise ValueError("Selected component exceeds 512 MiB limit")
            h = hashlib.sha256()
            with z.open(info) as src:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    h.update(chunk)
            component = {"basename": name, "size": info.file_size, "sha256": h.hexdigest()}
            if name in EXPECTED:
                component["expected_baseline_match"] = (info.file_size, h.hexdigest()) == EXPECTED[name]
            if extract:
                # Flat, numbered output names avoid traversal, symlinks, collisions,
                # and mixing binaries from multiple ABIs.
                dest = Path(extract) / f"{index:05d}-{name}"
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open("xb") as out, z.open(info) as src:
                    for chunk in iter(lambda: src.read(1024 * 1024), b""):
                        out.write(chunk)
                component["local_extracted_path"] = str(dest.resolve())
            result["selected_components"].append(component)
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("paths", nargs="+")
    p.add_argument("--extract-needed", type=Path)
    args = p.parse_args()
    print(json.dumps([inspect(x, args.extract_needed) for x in args.paths], indent=2))

if __name__ == "__main__":
    main()
