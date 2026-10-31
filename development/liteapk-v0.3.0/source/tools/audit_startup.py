#!/usr/bin/env python3
"""Static ELF/JNI audit. Does not load, execute, or modify the supplied .so.

The registration decoder is deliberately fingerprinted to the attached library.
Addresses in this decoder refer ONLY to this startup library, never gameplay.
"""
import argparse
import csv
import hashlib
import json
import re
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile

FINGERPRINT = "0cafd642bf5f1d97b4b09976c4d08ed55255e20962727da9f78b0943b44c6b1a"

def audit(path, output):
    path, output = Path(path), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    with path.open("rb") as f:
        elf = ELFFile(f)
        segments = [s for s in elf.iter_segments() if s["p_type"] == "PT_LOAD"]
        def read(address, length):
            for s in segments:
                delta = address - s["p_vaddr"]
                if 0 <= delta <= s["p_filesz"] and length <= s["p_filesz"] - delta:
                    off = s["p_offset"] + delta
                    return raw[off:off + length]
            raise ValueError(f"Unmapped ELF VA: {address:#x}, length {length}")
        def cstring(address):
            b = bytearray()
            for i in range(4096):
                c = read(address + i, 1)
                if c == b"\0":
                    return b.decode("utf-8", "strict")
                b.extend(c)
            raise ValueError("Unterminated ELF string")
        dyn = elf.get_section_by_name(".dynamic")
        deps = [x.needed for x in dyn.iter_tags() if x.entry.d_tag == "DT_NEEDED"]
        symbols = elf.get_section_by_name(".dynsym")
        imports = [s.name for s in symbols.iter_symbols() if s["st_shndx"] == "SHN_UNDEF" and s.name]
        strings = [m.group().decode("ascii") for m in re.finditer(rb"[\x20-\x7e]{5,}", raw)]
        urls = sorted({u for text in strings for u in re.findall(r'https?://[^\s<>";]+', text)})
        report = {"filename": "libandroidoyunclub.so", "sha256": sha, "size": len(raw),
                  "elf_class": elf.elfclass, "machine": elf["e_machine"], "needed": deps,
                  "imports": imports, "plaintext_urls": urls,
                  "checkupdate_plaintext_references": [s for s in strings if "checkupdate" in s.lower()],
                  "writable_executable_segments": sum((s["p_flags"] & 3) == 3 for s in segments),
                  "gnu_relro_present": any(s["p_type"] == "PT_GNU_RELRO" for s in elf.iter_segments()),
                  "executable_stack": any(s["p_type"] == "PT_GNU_STACK" and (s["p_flags"] & 1)
                                          for s in elf.iter_segments()),
                  "runtime_security_test": "NOT PERFORMED", "gameplay_mod_identification": "UNRESOLVED"}
        if sha != FINGERPRINT:
            report["registration_decoder"] = "BLOCKED: fingerprint mismatch"
        else:
            rel = {r["r_offset"]: r["r_addend"]
                   for r in elf.get_section_by_name(".rela.dyn").iter_relocations()
                   if r["r_info_type"] == 1027}  # R_AARCH64_RELATIVE
            def ptr(address):
                return rel.get(address, struct.unpack("<Q", read(address, 8))[0])
            dis = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
            functions = {}
            for name in ("JNI_OnLoad", "Java_androidoyunclub_androidoyunclub_register"):
                symbol = symbols.get_symbol_by_name(name)[0]
                ins = list(dis.disasm(read(symbol["st_value"], symbol["st_size"]), symbol["st_value"]))
                functions[name] = ins
                (output / (name + ".asm")).write_text("\n".join(
                    f"{i.address:08x}: {i.mnemonic:8s} {i.op_str}" for i in ins) + "\n")
            instructions = {i.address: i for i in functions["Java_androidoyunclub_androidoyunclub_register"]}
            jumps = struct.unpack("<124H", read(0x24c66, 248))
            rows = []
            for register_id, jump in enumerate(jumps):
                pc, table, count = 0xbf1d8 + jump * 4, None, None
                for _ in range(100):
                    i = instructions.get(pc)
                    if i is None:
                        raise ValueError("Unexpected JNI registration control flow")
                    if i.mnemonic == "adr" and i.op_str.startswith(("x8, #0xe", "x1, #0xe")):
                        a = int(i.op_str.split("#")[1], 16)
                        if table is None and 0xe1cc0 <= a < 0xe8000:
                            table = a
                    if i.mnemonic == "mov" and i.op_str.startswith("w3, #"):
                        count = int(i.op_str.split("#")[1], 0)
                    if i.mnemonic == "b":
                        pc = int(i.op_str[1:], 16)
                        continue
                    if i.mnemonic == "blr" and count is not None:
                        break
                    pc += 4
                if table is None or count is None:
                    raise ValueError("Incomplete registration case")
                for index in range(count):
                    a = table + index * 24
                    name, signature, function = cstring(ptr(a)), cstring(ptr(a + 8)), ptr(a + 16)
                    if not signature.startswith("(") or ")" not in signature:
                        raise ValueError("Invalid JNI signature in decoded table")
                    if not any(s["p_flags"] & 1 and s["p_vaddr"] <= function < s["p_vaddr"] + s["p_filesz"]
                               for s in segments):
                        raise ValueError("JNI function points outside executable segments")
                    rows.append({"register_id": register_id, "entry": index, "table_va": hex(table),
                                 "name": name, "signature": signature, "function_va": hex(function)})
            with (output / "native_registrations.csv").open("w", newline="") as out:
                writer = csv.DictWriter(out, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
            report.update(registration_groups=len(jumps), registered_methods=len(rows),
                          registration_decoder="VERIFIED STATIC TABLE DECODE",
                          register52_methods=[r["name"] for r in rows if r["register_id"] == 52])
        (output / "native_audit.json").write_text(json.dumps(report, indent=2) + "\n")
        return report

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("library", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    r = audit(a.library, a.output)
    print(json.dumps({k: r.get(k) for k in ["sha256", "size", "machine", "registration_groups",
                                           "registered_methods", "registration_decoder"]}, indent=2))
