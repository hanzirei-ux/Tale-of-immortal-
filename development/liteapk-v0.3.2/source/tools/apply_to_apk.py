#!/usr/bin/env python3
"""Apply this exact-baseline patch to a complete, local APK. Output is UNSIGNED.

The extraction is not itself an APK. This tool never reads/writes phone saves,
downloads a game, removes a startup dependency, or supplies a signing key.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

GAME_ACTIVITY = "com.guigugame.guigubahuangoverseas.OverrideActivity"
ANDROID = "http://schemas.android.com/apk/res/android"
SIGNATURE = re.compile(r"^META-INF/(?:[^/]+\.(?:SF|RSA|DSA|EC)|MANIFEST\.MF)$", re.I)


def digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(block)
    return h.hexdigest()


def axml_elements(data):
    """Decode only names/attributes needed for manifest inspection, not resources."""
    if data.lstrip().startswith(b"<"):
        root = ET.fromstring(data)
        def walk(node):
            yield True, node.tag, {k.rsplit("}", 1)[-1]: v for k, v in node.attrib.items()}
            for child in node:
                yield from walk(child)
            yield False, node.tag, {}
        return list(walk(root))
    if len(data) < 8 or struct.unpack_from("<H", data)[0] != 3:
        raise ValueError("AndroidManifest.xml is not recognized XML/AXML")
    strings, elements = [], []
    cursor = struct.unpack_from("<H", data, 2)[0]
    while cursor < len(data):
        if cursor + 8 > len(data):
            raise ValueError("Truncated AXML chunk")
        kind, header, size = struct.unpack_from("<HHI", data, cursor)
        if size < header or header < 8 or cursor + size > len(data):
            raise ValueError("Invalid AXML chunk bounds")
        chunk = data[cursor:cursor + size]
        if kind == 1:
            count, _, flags, start, _ = struct.unpack_from("<5I", chunk, 8)
            if count > 100000 or header + count * 4 > size:
                raise ValueError("Invalid AXML string pool")
            def length_at(pos, utf8):
                if utf8:
                    a = chunk[pos]
                    return (((a & 127) << 8) | chunk[pos + 1], pos + 2) if a & 128 else (a, pos + 1)
                a = struct.unpack_from("<H", chunk, pos)[0]
                return (((a & 32767) << 16) | struct.unpack_from("<H", chunk, pos + 2)[0], pos + 4) if a & 32768 else (a, pos + 2)
            for i in range(count):
                at = start + struct.unpack_from("<I", chunk, header + i * 4)[0]
                if flags & 256:
                    _, at = length_at(at, True)
                    n, at = length_at(at, True)
                    strings.append(chunk[at:at + n].decode("utf-8"))
                else:
                    n, at = length_at(at, False)
                    strings.append(chunk[at:at + n * 2].decode("utf-16le"))
        elif kind == 0x102:
            _, name, attr_start, attr_size, count = struct.unpack_from("<IIHHH", chunk, 16)
            if attr_size < 20 or 16 + attr_start + count * attr_size > size:
                raise ValueError("Invalid AXML attributes")
            attrs = {}
            for i in range(count):
                at = 16 + attr_start + i * attr_size
                _, key, raw, _, _, value_type, value = struct.unpack_from("<IIIHBBI", chunk, at)
                attrs[strings[key]] = strings[raw] if raw != 0xffffffff else strings[value] if value_type == 3 else value
            elements.append((True, strings[name], attrs))
        elif kind == 0x103:
            elements.append((False, strings[struct.unpack_from("<I", chunk, 20)[0]], {}))
        cursor += size
    return elements


def inspect_manifest(data):
    package, declared, launchers = "", [], []
    activity = None
    current_filter = None
    def qualify(name):
        return package + name if name.startswith(".") else package + "." + name if "." not in name else name
    for opening, tag, attrs in axml_elements(data):
        if opening and tag == "manifest":
            package = str(attrs.get("package", ""))
        elif opening and tag in {"activity", "activity-alias"}:
            name = qualify(str(attrs.get("name", "")))
            target = qualify(str(attrs.get("targetActivity", attrs.get("name", ""))))
            declared.append(name)
            activity = target
        elif opening and tag == "intent-filter" and activity:
            current_filter = set()
        elif opening and tag in {"action", "category"} and current_filter is not None:
            current_filter.add(attrs.get("name"))
        elif not opening and tag == "intent-filter" and current_filter is not None:
            if {"android.intent.action.MAIN", "android.intent.category.LAUNCHER"} <= current_filter:
                launchers.append(activity)
            current_filter = None
        elif not opening and tag in {"activity", "activity-alias"}:
            activity = None
    if not package:
        raise ValueError("Manifest package is unavailable")
    return {"package": package, "activities": declared, "launcher_targets": launchers}


def aligned_info(name, output_position, compression, original=None):
    info = zipfile.ZipInfo(name, original.date_time if original else (2026, 10, 31, 0, 0, 0))
    info.compress_type = compression
    if original:
        info.external_attr, info.internal_attr = original.external_attr, original.internal_attr
        info.create_system, info.comment = original.create_system, original.comment
    if compression == zipfile.ZIP_STORED:
        alignment = 16384 if name.endswith(".so") else 4
        encoded = name.encode("ascii") if name.isascii() else name.encode("utf-8")
        padding = (-(output_position + 30 + len(encoded) + 4)) % alignment
        info.extra = struct.pack("<HH", 0xA11E, padding) + b"\0" * padding
    return info


def check_alignment(path):
    with zipfile.ZipFile(path) as z, open(path, "rb") as f:
        for entry in z.infolist():
            if entry.compress_type != zipfile.ZIP_STORED:
                continue
            f.seek(entry.header_offset + 26)
            a, b = struct.unpack("<HH", f.read(4))
            offset = entry.header_offset + 30 + a + b
            if offset % (16384 if entry.filename.endswith(".so") else 4):
                raise ValueError("ZIP data alignment failed: " + entry.filename)


def apply_patch(source, output, patch_dir, metadata=None, indirect_activity=False):
    source, output, patch_dir = Path(source), Path(output), Path(patch_dir)
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError("Output must be a NEW file, different from the original APK")
    manifest = json.loads((patch_dir / "patch_manifest.json").read_text())
    for name, expected in manifest["files"].items():
        p = patch_dir / name
        if p.resolve().parent != patch_dir.resolve() and patch_dir.resolve() not in p.resolve().parents:
            raise ValueError("Invalid patch path")
        with p.open("rb") as f:
            if digest(f) != expected["sha256"]:
                raise ValueError("Patch component checksum failed: " + name)
    with zipfile.ZipFile(source) as zin:
        names = zin.namelist()
        if len(names) != len(set(names)) or any(n.startswith("/") or ".." in n.split("/") for n in names):
            raise ValueError("Ambiguous or unsafe ZIP paths")
        for name, expected in manifest["baseline_apk_entries"].items():
            with zin.open(name) as f:
                if digest(f) != expected:
                    raise ValueError("Baseline checksum failed: " + name)
        app = inspect_manifest(zin.read("AndroidManifest.xml"))
        if GAME_ACTIVITY not in app["activities"]:
            raise ValueError("Verified game Activity is not declared in this APK")
        if GAME_ACTIVITY not in app["launcher_targets"] and not indirect_activity:
            raise ValueError("Launcher is indirect. Inspect its route to OverrideActivity before using --allow-indirect-launcher")
        if any(n.startswith("org/npc/toibridge") for n in names) or "lib/arm64-v8a/libtoimodmenu.so" in names:
            raise ValueError("This APK may already contain the mod; use the original baseline")
        common = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
        fallback = "assets/toimod/global-metadata.dat"
        metadata_name = common if common in names else fallback if fallback in names else None
        if metadata_name:
            with zin.open(metadata_name) as f:
                if digest(f) != manifest["metadata_sha256"]:
                    raise ValueError("Metadata checksum mismatch")
        elif not metadata:
            raise ValueError("Metadata asset missing: provide the original with --metadata")
        else:
            with Path(metadata).open("rb") as f:
                if digest(f) != manifest["metadata_sha256"]:
                    raise ValueError("Provided metadata checksum mismatch")
        indices = [int(m.group(1) or 1) for n in names if (m := re.fullmatch(r"classes(\d*)\.dex", n))]
        helper_name = "classes" + str(max(indices, default=1) + 1) + ".dex"
        replacements = {"classes.dex": patch_dir / "classes.dex"}
        additions = {helper_name: patch_dir / "toimodmenu.dex", "lib/arm64-v8a/libtoimodmenu.so": patch_dir / "lib/arm64-v8a/libtoimodmenu.so"}
        if not metadata_name:
            additions[fallback] = Path(metadata)
        output.parent.mkdir(parents=True, exist_ok=True)
        created = False
        try:
            with output.open("xb") as destination:
                created = True
                with zipfile.ZipFile(destination, "w", allowZip64=True) as zout:
                    for entry in zin.infolist():
                        if SIGNATURE.fullmatch(entry.filename):
                            continue
                        if entry.flag_bits & 1:
                            raise ValueError("Encrypted APK entry unsupported")
                        compression = zipfile.ZIP_STORED if entry.filename.endswith(".so") else entry.compress_type
                        info = aligned_info(entry.filename, destination.tell(), compression, entry)
                        with zout.open(info, "w", force_zip64=entry.file_size >= 2**31) as target:
                            if entry.filename in replacements:
                                with replacements[entry.filename].open("rb") as f:
                                    shutil.copyfileobj(f, target, 1024 * 1024)
                            else:
                                with zin.open(entry) as f:
                                    shutil.copyfileobj(f, target, 1024 * 1024)
                    for name, path in additions.items():
                        compression = zipfile.ZIP_STORED if name.endswith(".so") else zipfile.ZIP_DEFLATED
                        info = aligned_info(name, destination.tell(), compression)
                        with zout.open(info, "w", force_zip64=path.stat().st_size >= 2**31) as target, path.open("rb") as f:
                            shutil.copyfileobj(f, target, 1024 * 1024)
            check_alignment(output)
        except BaseException:
            if created:
                output.unlink(missing_ok=True)
            raise
    with output.open("rb") as f:
        checksum = digest(f)
    receipt = {"output": str(output), "sha256": checksum, "signed": False, "device_tested": False,
               "helper_dex": helper_name, "manifest": app, "indirect_launcher_acknowledged": indirect_activity,
               "libil2cpp_modified": False, "startup_dependencies_removed": False}
    Path(str(output) + ".report.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_apk", type=Path)
    p.add_argument("output_unsigned_apk", type=Path)
    p.add_argument("--patch-dir", type=Path, default=Path(__file__).resolve().parents[1] / "patch")
    p.add_argument("--metadata", type=Path)
    p.add_argument("--allow-indirect-launcher", action="store_true", help="Only after inspecting the launcher's route to OverrideActivity")
    args = p.parse_args()
    try:
        print(json.dumps(apply_patch(args.original_apk, args.output_unsigned_apk, args.patch_dir, args.metadata, args.allow_indirect_launcher), indent=2))
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, struct.error, IndexError) as exc:
        p.exit(1, "REFUSED: " + str(exc) + "\n")
