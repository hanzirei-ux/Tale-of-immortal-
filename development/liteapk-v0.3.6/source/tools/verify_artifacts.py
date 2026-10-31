#!/usr/bin/env python3
"""Static artifact verification. A successful result is NOT a gameplay test."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib
from elftools.elf.elffile import ELFFile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dex_info(path):
    b = Path(path).read_bytes()
    if b[:8] not in (b"dex\n035\0", b"dex\n037\0", b"dex\n038\0", b"dex\n039\0"):
        raise ValueError("Unsupported DEX magic")
    if len(b) < 112 or struct.unpack_from("<III", b, 32) != (len(b), 112, 0x12345678):
        raise ValueError("DEX header size/endian mismatch")
    if b[12:32] != hashlib.sha1(b[32:]).digest() or struct.unpack_from("<I", b, 8)[0] != zlib.adler32(b[12:]):
        raise ValueError("DEX SHA-1/Adler32 mismatch")
    def u32(offset):
        return struct.unpack_from("<I", b, offset)[0]
    def uleb(offset):
        v = 0
        for shift in range(0, 35, 7):
            c = b[offset];offset += 1;v |= (c & 127) << shift
            if not c & 128:
                return v, offset
        raise ValueError("Invalid ULEB128")
    strings = []
    for i in range(u32(56)):
        at = u32(u32(60) + i * 4)
        _, at = uleb(at)
        end = b.index(0, at)
        strings.append(b[at:end].replace(b"\xc0\x80", b"\0").decode("utf-8", "surrogatepass"))
    types = [strings[u32(u32(68) + i * 4)] for i in range(u32(64))]
    protos = []
    for i in range(u32(72)):
        _, ret, params = struct.unpack_from("<III", b, u32(76) + i * 12)
        args = "" if not params else "".join(types[struct.unpack_from("<H", b, params + 4 + j * 2)[0]] for j in range(u32(params)))
        protos.append("(" + args + ")" + types[ret])
    method_refs = []
    for i in range(u32(88)):
        owner, proto, name = struct.unpack_from("<HHI", b, u32(92) + i * 8)
        method_refs.append(types[owner] + "->" + strings[name] + protos[proto])
    classes, methods, native = set(), {}, {}
    for i in range(u32(96)):
        fields = struct.unpack_from("<8I", b, u32(100) + i * 32)
        owner, data = types[fields[0]], fields[6]
        classes.add(owner)
        if not data:
            continue
        counts = []
        for _ in range(4):
            n, data = uleb(data);counts.append(n)
        for _ in range(counts[0] + counts[1]):
            _, data = uleb(data);_, data = uleb(data)
        for count in counts[2:]:
            index = 0
            for _ in range(count):
                delta, data = uleb(data);flags, data = uleb(data);_, data = uleb(data)
                index += delta
                methods[method_refs[index]] = flags
                if flags & 0x100:
                    native[method_refs[index]] = flags
    return {"size": len(b), "sha256": sha(path), "version": b[4:7].decode(), "class_count": len(classes),
            "method_reference_count": len(method_refs), "classes": sorted(classes), "methods": methods, "native_methods": native}


def verify(patch_dir, source_root, original_dex=None, game_lib=None):
    patch_dir, source_root = Path(patch_dir), Path(source_root)
    patched = dex_info(patch_dir / "classes.dex")
    helper = dex_info(patch_dir / "toimodmenu.dex")
    if set(patched["classes"]) & set(helper["classes"]):
        raise ValueError("Duplicate class across original and helper DEX")
    for name in ("Lorg/npc/toibridge/ModMenu;", "Lorg/npc/toibridge/NativeBridge;"):
        if name not in helper["classes"]:
            raise ValueError("Missing helper class: " + name)
    dex_comparison = None
    if original_dex:
        original = dex_info(original_dex)
        if original["classes"] != patched["classes"] or original["native_methods"] != patched["native_methods"]:
            raise ValueError("Original classes or registered native signatures changed")
        removed = set(original["methods"]) - set(patched["methods"])
        added = set(patched["methods"]) - set(original["methods"])
        expected = {"Lcom/guigugame/guigubahuangoverseas/OverrideActivity;->onCreate(Landroid/os/Bundle;)V",
                    "Lcom/guigugame/guigubahuangoverseas/OverrideActivity;->onDestroy()V"}
        if removed or added != expected or any(patched["methods"][m] != f for m, f in original["methods"].items()):
            raise ValueError("DEX method changes exceed the intended Activity patch")
        dex_comparison = {"original_sha256": original["sha256"], "added_methods": sorted(added),
                          "removed_methods": [], "all_original_native_signatures_identical": True}
    library = patch_dir / "lib/arm64-v8a/libtoimodmenu.so"
    with library.open("rb") as f:
        elf = ELFFile(f)
        if elf.elfclass != 64 or elf["e_machine"] != "EM_AARCH64" or elf["e_type"] != "ET_DYN":
            raise ValueError("Native component is not an AArch64 shared object")
        segments = list(elf.iter_segments())
        loads = [s for s in segments if s["p_type"] == "PT_LOAD"]
        if not loads or any(s["p_align"] < 16384 for s in loads):
            raise ValueError("Native LOAD segment alignment below 16 KiB")
        if not any(s["p_type"] == "PT_GNU_RELRO" for s in segments):
            raise ValueError("Missing RELRO")
        if any(s["p_type"] == "PT_GNU_STACK" and s["p_flags"] & 1 for s in segments):
            raise ValueError("Executable stack")
        dynamic = elf.get_section_by_name(".dynamic")
        needed = [t.needed for t in dynamic.iter_tags() if t.entry.d_tag == "DT_NEEDED"]
        if set(needed) - {"libdl.so", "liblog.so", "libm.so", "libc.so"}:
            raise ValueError("Unexpected non-system shared dependency: " + repr(needed))
        exports = {s.name for s in elf.get_section_by_name(".dynsym").iter_symbols() if s["st_shndx"] != "SHN_UNDEF"}
        java = (source_root / "android/bridge/src/main/java/org/npc/toibridge/NativeBridge.java").read_text()
        jni_names = ["Java_org_npc_toibridge_NativeBridge_" + s for s in re.findall(r"public static native \S+ (\w+)\(", java)]
        missing = set(jni_names + ["JNI_OnLoad", "toi_bridge_pump", "toi_mod_abi_version"]) - exports
        if missing:
            raise ValueError("Missing native exports: " + repr(missing))
    profile = json.loads((source_root / "native/baseline_profile.json").read_text())
    verified_sites = 0
    if game_lib:
        if sha(game_lib) != profile["baseline_sha256"]:
            raise ValueError("Game library differs from hook profile")
        with open(game_lib, "rb") as f:
            elf = ELFFile(f)
            raw = Path(game_lib).read_bytes()
            for item in profile["methods"].values():
                a, at = item["Address"], item["FileOffset"]
                if not any(s["p_type"] == "PT_LOAD" and s["p_flags"] & 1 and s["p_vaddr"] <= a < s["p_vaddr"] + s["p_filesz"] for s in elf.iter_segments()):
                    raise ValueError("Hook target outside executable mapping")
                if raw[at:at + 16].hex() != item["Prologue16"]:
                    raise ValueError("Hook prologue mismatch")
                verified_sites += 1
    compact = lambda d: {k: v for k, v in d.items() if k not in {"classes", "methods", "native_methods"}}
    return {"status": "IMPLEMENTED — STATIC VERIFIED", "device_tested": False,
            "patched_dex": compact(patched), "helper_dex": compact(helper), "dex_comparison": dex_comparison,
            "native": {"sha256": sha(library), "size": library.stat().st_size, "abi": "arm64-v8a", "needed": needed,
                       "jni_methods_exported": len(jni_names), "load_alignment": 16384, "relro": True, "executable_stack": False},
            "game_profile_sites_verified": verified_sites}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--patch-dir", type=Path, default=Path(__file__).resolve().parents[1] / "patch")
    p.add_argument("--original-dex", type=Path)
    p.add_argument("--game-lib", type=Path)
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    report = verify(a.patch_dir, Path(__file__).resolve().parents[1], a.original_dex, a.game_lib)
    out = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(out)
    print(out)
