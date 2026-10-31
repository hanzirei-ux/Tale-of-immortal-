#!/usr/bin/env python3
"""Bounds-checked v31 metadata probe extending research v1. No RVA guessing.

TypeIndex is an index into native IL2CPP type registration, NOT a managed name.
Resolve actual parameter/return types against the matching library/runtime.
"""
import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path

BASELINE_HASH = "9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3"
TARGETS = {"GMCmd", "EditorCommand", "UI_EditorTest1Cmd", "GMCmdTool", "GMFunc",
           "UI_EditorTest6", "UIPlayerBagExtend", "ConfMakePillFormula", "UIPillFormulaView",
           "UnitySynchronizationContext", "SynchronizationContext", "Thread"}

class InvalidMetadata(ValueError):
    pass

class MetadataV31:
    def __init__(self, data):
        self.data = data
        if len(data) < 256:
            raise InvalidMetadata("Truncated header")
        self.h = struct.unpack_from("<64I", data)
        if self.h[:2] != (0xFAB11BAF, 31):
            raise InvalidMetadata("Only metadata magic FAB11BAF, version 31 is supported")
        self.strings = self.table(6, 1)
        self.methods = self.table(12, 36)
        self.parameters = self.table(22, 12)
        self.fields = self.table(24, 12)
        self.types = self.table(40, 88)
        self.images = self.table(42, 40)

    def table(self, index, stride):
        offset, size = self.h[index:index + 2]
        if size % stride or offset > len(self.data) or size > len(self.data) - offset:
            raise InvalidMetadata(f"Table at header {index} is misaligned or out of bounds")
        if size and offset < 256:
            raise InvalidMetadata("Nonempty table overlaps the header")
        return self.data[offset:offset + size]

    def string(self, index):
        if index < 0 or index >= len(self.strings):
            raise InvalidMetadata("Metadata string index is out of bounds")
        end = self.strings.find(b"\0", index)
        if end < 0:
            raise InvalidMetadata("Unterminated metadata string")
        return self.strings[index:end].decode("utf-8", "strict")

    def report(self):
        images = []
        for row in struct.iter_unpack("<10I", self.images):
            name, start, count = self.string(row[0]), row[2], row[3]
            if start > len(self.types) // 88 or count > len(self.types) // 88 - start:
                raise InvalidMetadata("Image type range is invalid")
            images.append((name, start, count))
        rows = []
        for type_index, t in enumerate(struct.iter_unpack("<16I8H2I", self.types)):
            name, ns = self.string(t[0]), self.string(t[1])
            if name not in TARGETS:
                continue
            image = next((n for n, a, c in images if a <= type_index < a + c), None)
            start, count = t[9], t[16]
            if start > len(self.methods) // 36 or count > len(self.methods) // 36 - start:
                raise InvalidMetadata("Type method range is invalid")
            for index in range(start, start + count):
                m = struct.unpack_from("<7I4H", self.methods, index * 36)
                if m[1] != type_index:
                    raise InvalidMetadata("Method owner does not match containing type")
                pstart, pcount = m[4], m[10]  # v31 includes returnParameterToken at m[3]
                params = []
                if pcount:
                    if pstart > len(self.parameters) // 12 or pcount > len(self.parameters) // 12 - pstart:
                        raise InvalidMetadata("Method parameter range is invalid")
                    for pindex in range(pstart, pstart + pcount):
                        p = struct.unpack_from("<IIi", self.parameters, pindex * 12)
                        params.append({"name": self.string(p[0]), "type_index": p[2], "token": hex(p[1])})
                rows.append({"image": image, "namespace": ns, "type": name, "type_index": type_index,
                             "method": self.string(m[0]), "method_index": index,
                             "token": f"0x{m[6]:08x}", "return_type_index": m[2],
                             "return_parameter_token": hex(m[3]), "flags": hex(m[7]),
                             "static": bool(m[7] & 0x10), "parameter_count": pcount,
                             "parameters": params, "runtime_address": None,
                             "status": "MAPPED ONLY"})
        return {"metadata_version": 31, "type_count": len(self.types) // 88,
                "method_count": len(self.methods) // 36, "image_count": len(images), "targets": rows}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("metadata", type=Path)
    p.add_argument("--expect-baseline", action="store_true")
    p.add_argument("--methods-csv", type=Path, help="Write selected methods in the existing mapping CSV format")
    args = p.parse_args()
    data = args.metadata.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if args.expect_baseline and sha != BASELINE_HASH:
        p.error("Metadata hash mismatch; refusing to label this as the LiteAPK baseline")
    report = MetadataV31(data).report()
    report["sha256"] = sha
    report["specified_baseline_match"] = sha == BASELINE_HASH
    if args.methods_csv:
        with args.methods_csv.open("x", encoding="utf-8-sig", newline="") as f:
            fields = ["image", "type", "type_index", "method", "method_index", "parameters", "method_token"]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for m in report["targets"]:
                writer.writerow({"image": m["image"], "type": m["type"], "type_index": m["type_index"],
                                 "method": m["method"], "method_index": m["method_index"],
                                 "parameters": m["parameter_count"], "method_token": m["token"]})
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
