#!/usr/bin/env python3
"""Find an ARM64 codegen module structurally, then map metadata TOKENS to VAs.

Requires the actual matching libil2cpp.so. Never uses an old V60 RVA. Candidate
structures are hypotheses until their complete pointer table passes validation.
No files are modified; ELF VAs still require the runtime load base for ASLR.
Supports ordinary AArch64 RELA relative relocations, not Android packed/RELR.
"""
import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile

BASELINE_HASH = "c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099"

def resolve(library, methods, allow_other=False, assembly="Assembly-CSharp.dll"):
    raw = Path(library).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != BASELINE_HASH and not allow_other:
        raise ValueError("Library hash mismatch: this is not the specified LiteAPK baseline")
    with Path(library).open("rb") as f:
        elf = ELFFile(f)
        if elf.elfclass != 64 or not elf.little_endian or elf["e_machine"] != "EM_AARCH64":
            raise ValueError("Only little-endian AArch64 ELF64 supported")
        segments = [s for s in elf.iter_segments() if s["p_type"] == "PT_LOAD"]
        def offset(address, length=1):
            for s in segments:
                delta = address - s["p_vaddr"]
                if 0 <= delta <= s["p_filesz"] and length <= s["p_filesz"] - delta:
                    return s["p_offset"] + delta
            raise ValueError("Pointer outside file-backed PT_LOAD")
        def read64(address):
            return struct.unpack_from("<Q", raw, offset(address, 8))[0]
        relocations = {}
        for section in elf.iter_sections():
            if section["sh_type"] == "SHT_RELR" or section.name in {".android.rela.dyn", ".android.rel.dyn"}:
                raise ValueError("Packed/RELR relocations need a verified decoder; not guessed")
            if section["sh_type"] == "SHT_RELA":
                for r in section.iter_relocations():
                    if r["r_info_type"] == 1027:
                        relocations[r["r_offset"]] = r["r_addend"]
        def pointer(address):
            return relocations.get(address, read64(address))
        needle = assembly.encode("ascii") + b"\0"
        names = set()
        at = raw.find(needle)
        while at >= 0:
            for s in segments:
                if s["p_offset"] <= at < s["p_offset"] + s["p_filesz"]:
                    names.add(s["p_vaddr"] + at - s["p_offset"])
            at = raw.find(needle, at + 1)
        with Path(methods).open(encoding="utf-8-sig") as src:
            rows = [r for r in csv.DictReader(src) if r["image"] == assembly]
        if not rows:
            raise ValueError("No metadata method tokens for the requested assembly")
        maximum = max((int(r["method_token"], 16) & 0xffffff for r in rows), default=1)
        candidates = []
        for address, target in relocations.items():
            if target not in names:
                continue
            try:
                count_raw = read64(address + 8)
                if not maximum <= count_raw <= 1_000_000:
                    continue
                table = pointer(address + 16)
                offset(table, count_raw * 8)
                populated = 0
                for i in range(count_raw):
                    function = pointer(table + i * 8)
                    if function == 0:
                        continue
                    if function % 4 or not any(s["p_flags"] & 1 and s["p_vaddr"] <= function < s["p_vaddr"] + s["p_filesz"]
                                               for s in segments):
                        raise ValueError("Invalid executable method pointer")
                    populated += 1
                if populated:
                    candidates.append((address, count_raw, table))
            except (ValueError, struct.error):
                continue
        if len(candidates) != 1:
            raise ValueError(f"Expected one validated codegen module, found {len(candidates)}")
        module, count, table = candidates[0]
        mapped = []
        for r in rows:
            token = int(r["method_token"], 16)
            if token >> 24 != 6 or not 1 <= (token & 0xffffff) <= count:
                raise ValueError("Invalid MethodDef token for selected module")
            function = pointer(table + ((token & 0xffffff) - 1) * 8)
            mapped.append({"type": r["type"], "method": r["method"],
                           "metadata_index_reference_only": int(r["method_index"]),
                           "token": hex(token), "elf_va": hex(function) if function else None,
                           "file_offset": hex(offset(function)) if function else None,
                           "status": "MAPPED ONLY" if function else "NO NONNULL POINTER"})
        return {"sha256": sha, "specified_baseline_match": sha == BASELINE_HASH,
                "assembly": assembly,
                "module_va": hex(module), "pointer_table_va": hex(table), "method_pointer_count": count,
                "address_note": "ELF VA; runtime ASLR load base required. No gameplay validation.",
                "methods": mapped}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("library", type=Path)
    p.add_argument("methods_csv", type=Path)
    p.add_argument("--allow-other-binary", action="store_true", help="Research only; never labels another binary compatible")
    p.add_argument("--assembly", default="Assembly-CSharp.dll")
    a = p.parse_args()
    print(json.dumps(resolve(a.library, a.methods_csv, a.allow_other_binary, a.assembly), indent=2))
