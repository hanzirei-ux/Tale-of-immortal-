import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from apply_to_apk import GAME_ACTIVITY, apply_patch, inspect_manifest, check_alignment

XML = f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.guigugame.guigubahuangoverseas">
<application><activity android:name="{GAME_ACTIVITY}"><intent-filter>
<action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/>
</intent-filter></activity></application></manifest>'''.encode()


class ApkPatchTests(unittest.TestCase):
    def fixture(self, folder, manifest_xml=XML, with_metadata=True):
        folder = Path(folder)
        patch = folder / "patch"
        (patch / "lib/arm64-v8a").mkdir(parents=True)
        files = {"classes.dex": b"patched fixture", "toimodmenu.dex": b"helper fixture",
                 "lib/arm64-v8a/libtoimodmenu.so": b"mod fixture"}
        for name, data in files.items():
            (patch / name).write_bytes(data)
        original = {"classes.dex": b"original fixture", "classes2.dex": b"keep existing secondary dex",
                    "lib/arm64-v8a/libil2cpp.so": b"game fixture", "lib/arm64-v8a/libandroidoyunclub.so": b"startup fixture",
                    "AndroidManifest.xml": manifest_xml, "resources.arsc": b"resources fixture",
                    "assets/game.dat": b"asset fixture", "META-INF/CERT.RSA": b"old signature",
                    "META-INF/CERT.SF": b"old signature", "META-INF/MANIFEST.MF": b"old manifest",
                    "META-INF/services/fixture": b"must preserve"}
        meta = b"metadata fixture"
        if with_metadata:
            original["assets/bin/Data/Managed/Metadata/global-metadata.dat"] = meta
        sha = lambda b: hashlib.sha256(b).hexdigest()
        guards = {n: sha(original[n]) for n in ("classes.dex", "lib/arm64-v8a/libil2cpp.so", "lib/arm64-v8a/libandroidoyunclub.so")}
        (patch / "patch_manifest.json").write_text(json.dumps({"files": {n: {"sha256": sha(v)} for n, v in files.items()},
                                                              "baseline_apk_entries": guards, "metadata_sha256": sha(meta)}))
        source = folder / "baseline.apk"
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as z:
            for n, b in original.items():
                z.writestr(n, b)
        return source, folder / "test-unsigned.apk", patch, original

    def test_stream_patch_preserves_dependencies_assets_and_original(self):
        with tempfile.TemporaryDirectory() as d:
            source, output, patch, original = self.fixture(d)
            before = hashlib.sha256(source.read_bytes()).digest()
            report = apply_patch(source, output, patch)
            self.assertFalse(report["signed"])
            self.assertFalse(report["device_tested"])
            self.assertEqual(report["helper_dex"], "classes3.dex")
            self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), before)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(z.read("classes.dex"), b"patched fixture")
                self.assertEqual(z.read("classes3.dex"), b"helper fixture")
                for n in original:
                    if n != "classes.dex" and n not in {"META-INF/CERT.RSA", "META-INF/CERT.SF", "META-INF/MANIFEST.MF"}:
                        self.assertEqual(z.read(n), original[n], n)
                self.assertNotIn("META-INF/CERT.RSA", z.namelist())
                self.assertIsNone(z.testzip())
            check_alignment(output)

    def test_wrong_baseline_refused_without_output(self):
        with tempfile.TemporaryDirectory() as d:
            source, output, patch, _ = self.fixture(d)
            m = json.loads((patch / "patch_manifest.json").read_text())
            m["baseline_apk_entries"]["classes.dex"] = "0" * 64
            (patch / "patch_manifest.json").write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError, "Baseline checksum"):
                apply_patch(source, output, patch)
            self.assertFalse(output.exists())

    def test_modified_patch_refused(self):
        with tempfile.TemporaryDirectory() as d:
            source, output, patch, _ = self.fixture(d)
            (patch / "toimodmenu.dex").write_bytes(b"unexpected")
            with self.assertRaisesRegex(ValueError, "Patch component"):
                apply_patch(source, output, patch)

    def test_no_overwrite_of_any_existing_file(self):
        with tempfile.TemporaryDirectory() as d:
            source, output, patch, _ = self.fixture(d)
            output.write_bytes(b"keep me")
            with self.assertRaises(ValueError):
                apply_patch(source, output, patch)
            with self.assertRaises(ValueError):
                apply_patch(source, source, patch)
            self.assertEqual(output.read_bytes(), b"keep me")

    def test_missing_metadata_requires_exact_original(self):
        with tempfile.TemporaryDirectory() as d:
            source, output, patch, _ = self.fixture(d, with_metadata=False)
            with self.assertRaisesRegex(ValueError, "Metadata asset missing"):
                apply_patch(source, output, patch)
            meta = Path(d) / "metadata.dat"
            meta.write_bytes(b"wrong")
            with self.assertRaisesRegex(ValueError, "metadata checksum"):
                apply_patch(source, output, patch, meta)
            meta.write_bytes(b"metadata fixture")
            apply_patch(source, output, patch, meta)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(z.read("assets/toimod/global-metadata.dat"), meta.read_bytes())

    def test_indirect_launcher_is_explicit(self):
        xml = XML.replace(b"<activity android:name=", b"<activity android:name=", 1).replace(b"<intent-filter>", b"</activity><activity android:name=\".Protector\"><intent-filter>")
        with tempfile.TemporaryDirectory() as d:
            source, output, patch, _ = self.fixture(d, manifest_xml=xml)
            with self.assertRaisesRegex(ValueError, "Launcher is indirect"):
                apply_patch(source, output, patch)
            receipt = apply_patch(source, output, patch, indirect_activity=True)
            self.assertTrue(receipt["indirect_launcher_acknowledged"])

    def test_manifest_alias_resolves_target(self):
        xml = XML.replace(b"<intent-filter>", b"</activity><activity-alias android:name=\".Alias\" android:targetActivity=\".OverrideActivity\"><intent-filter>").replace(b"</activity></application>", b"</activity-alias></application>")
        self.assertEqual(inspect_manifest(xml)["launcher_targets"], [GAME_ACTIVITY])

    def test_binary_xml_string_pool_and_attributes(self):
        values = ["manifest", "package", "com.example", "application", "activity", "name", ".Main"]
        chunks, offsets, blob = [], [], bytearray()
        for value in values:
            offsets.append(len(blob))
            b = value.encode()
            blob.extend(bytes([len(value), len(b)]) + b + b"\0")
        start = 28 + len(values) * 4
        pool = struct.pack("<HHI5I", 1, 28, start + len(blob), len(values), 0, 256, start, 0)
        pool += struct.pack("<" + "I" * len(offsets), *offsets) + blob
        def begin(name, attrs=()):
            size = 36 + len(attrs) * 20
            out = struct.pack("<HHIII", 0x102, 16, size, 1, 0xffffffff)
            out += struct.pack("<II6H", 0xffffffff, name, 20, 20, len(attrs), 0, 0, 0)
            for key, value in attrs:
                out += struct.pack("<IIIHBBI", 0xffffffff, key, value, 8, 0, 3, value)
            return out
        def end(name):
            return struct.pack("<HHIIIII", 0x103, 16, 24, 1, 0xffffffff, 0xffffffff, name)
        data = pool + begin(0, [(1, 2)]) + begin(3) + begin(4, [(5, 6)]) + end(4) + end(3) + end(0)
        data = struct.pack("<HHI", 3, 8, len(data) + 8) + data
        self.assertEqual(inspect_manifest(data), {"package": "com.example", "activities": ["com.example.Main"], "launcher_targets": []})

    def test_malformed_binary_xml_refused(self):
        for data in (b"garbage", struct.pack("<HHIHHI", 3, 8, 16, 1, 28, 4)):
            with self.assertRaises((ValueError, struct.error, IndexError)):
                inspect_manifest(data)


if __name__ == "__main__":
    unittest.main()
