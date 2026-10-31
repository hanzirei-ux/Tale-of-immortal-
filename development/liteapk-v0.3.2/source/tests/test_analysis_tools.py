import csv
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from inspect_inputs import inspect, safe_member, private_member
from metadata_probe import MetadataV31, InvalidMetadata

def metadata_fixture():
    strings = bytearray(b"\0")
    def add(s):
        at = len(strings)
        strings.extend(s.encode() + b"\0")
        return at
    image, klass, method, arg = (add(x) for x in ["Assembly-CSharp.dll", "GMCmd", "CMDCall", "command"])
    h = [0] * 64
    h[0:2] = [0xFAB11BAF, 31]
    body = bytearray()
    def table(index, data):
        h[index:index+2] = [256 + len(body), len(data)]
        body.extend(data)
    table(6, strings)
    table(12, struct.pack("<7I4H", method, 0, 42, 0x08000001, 0, 0xffffffff,
                          0x0600a2c3, 0x16, 0, 0xffff, 1))
    table(22, struct.pack("<IIi", arg, 0x08000001, 55))
    table(24, b"")
    t = [0] * 26
    t[0], t[1], t[9], t[16] = klass, 0, 0, 1
    table(40, struct.pack("<16I8H2I", *t))
    table(42, struct.pack("<10I", image, 0, 0, 1, 0, 0, 0, 0, 0, 0))
    return bytearray(struct.pack("<64I", *h) + body)

class MetadataTests(unittest.TestCase):
    def test_v31_return_parameter_token_is_not_parameter_start(self):
        r = MetadataV31(metadata_fixture()).report()
        m = r["targets"][0]
        self.assertEqual((r["type_count"], r["method_count"], r["image_count"]), (1, 1, 1))
        self.assertEqual(m["token"], "0x0600a2c3")
        self.assertTrue(m["static"])
        self.assertEqual(m["return_parameter_token"], "0x8000001")
        self.assertEqual(m["parameters"], [{"name": "command", "type_index": 55, "token": "0x8000001"}])
        self.assertIsNone(m["runtime_address"])

    def test_wrong_version(self):
        b = metadata_fixture(); struct.pack_into("<I", b, 4, 29)
        with self.assertRaises(InvalidMetadata): MetadataV31(b)

    def test_truncation(self):
        with self.assertRaises(InvalidMetadata): MetadataV31(metadata_fixture()[:-1])

    def test_out_of_range_table(self):
        b = metadata_fixture(); struct.pack_into("<I", b, 12*4, 0xfffffff0)
        with self.assertRaises(InvalidMetadata): MetadataV31(b)

    def test_misaligned_table(self):
        b = metadata_fixture(); struct.pack_into("<I", b, 13*4, 35)
        with self.assertRaises(InvalidMetadata): MetadataV31(b)

    def test_bad_method_owner(self):
        b = metadata_fixture(); start = struct.unpack_from("<I", b, 12*4)[0]
        struct.pack_into("<I", b, start+4, 99)
        with self.assertRaises(InvalidMetadata): MetadataV31(b).report()

    def test_parameter_range(self):
        b = metadata_fixture(); start = struct.unpack_from("<I", b, 12*4)[0]
        struct.pack_into("<I", b, start+16, 0xffffff00)
        with self.assertRaises(InvalidMetadata): MetadataV31(b).report()

    def test_string_range(self):
        b = metadata_fixture(); start = struct.unpack_from("<I", b, 40*4)[0]
        struct.pack_into("<I", b, start, 0xffffff00)
        with self.assertRaises(InvalidMetadata): MetadataV31(b).report()

    def test_cli_csv_and_baseline_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p, out = Path(d)/"metadata.dat", Path(d)/"methods.csv"
            p.write_bytes(metadata_fixture())
            cli = [sys.executable, str(ROOT/"tools/metadata_probe.py"), str(p)]
            report = json.loads(subprocess.check_output(cli + ["--methods-csv", str(out)], text=True))
            self.assertFalse(report["specified_baseline_match"])
            with out.open(encoding="utf-8-sig") as f:
                row = list(csv.DictReader(f))[0]
            self.assertEqual(row["method_token"], "0x0600a2c3")
            self.assertEqual(row["parameters"], "1")
            refused = subprocess.run(cli + ["--expect-baseline"], capture_output=True, text=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("hash mismatch", refused.stderr)

class InputTests(unittest.TestCase):
    def test_missing_file_is_honest(self):
        self.assertEqual(inspect("/nonexistent/tales.zip")["status"], "MISSING")

    def test_sha_of_input(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"example"; p.write_bytes(b"abc")
            self.assertEqual(inspect(p)["sha256"], hashlib.sha256(b"abc").hexdigest())

    def test_private_data_excluded_from_selected_extraction(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"test.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("files/Save/world.dat", b"private-save")
                z.writestr("cache/libil2cpp.so", b"private-cache")
                z.writestr("lib/arm64-v8a/libil2cpp.so", b"research-binary")
            r = inspect(p, Path(d)/"out")
            self.assertEqual(r["private_entries_skipped"], 2)
            self.assertIsNone(r["crc_failure"])
            self.assertEqual(len(r["selected_components"]), 1)
            self.assertFalse(r["selected_components"][0]["expected_baseline_match"])
            self.assertEqual(next((Path(d)/"out").iterdir()).read_bytes(), b"research-binary")

    def test_zip_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"test.zip"
            with zipfile.ZipFile(p, "w") as z: z.writestr("../libil2cpp.so", b"x")
            with self.assertRaises(ValueError): inspect(p, Path(d)/"out")

    def test_extraction_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"test.zip"
            with zipfile.ZipFile(p, "w") as z: z.writestr("libil2cpp.so", b"x")
            inspect(p, Path(d)/"out")
            with self.assertRaises(FileExistsError): inspect(p, Path(d)/"out")

    def test_private_path_filters(self):
        self.assertTrue(private_member("Android/data/cache/unit"))
        self.assertFalse(safe_member("C:\\bad\\file"))
        self.assertFalse(safe_member("/bad/file"))

if __name__ == "__main__": unittest.main()
