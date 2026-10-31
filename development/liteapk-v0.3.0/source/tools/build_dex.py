#!/usr/bin/env python3
"""Reproduce the original DEX lifecycle patch and compile the Java menu DEX."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(*command):
    subprocess.run([str(x) for x in command], check=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_dex", type=Path)
    p.add_argument("--java-tools", type=Path, required=True)
    p.add_argument("--android-jar", type=Path, required=True, help="SDK platform 35 android.jar")
    p.add_argument("--java", default="java")
    a = p.parse_args()
    baseline = json.loads((ROOT / "config/baseline.json").read_text())
    if hashlib.sha256(a.original_dex.read_bytes()).hexdigest() != baseline["classes.dex"]["sha256"]:
        p.error("The original DEX is not the verified baseline")
    jars = json.loads((ROOT / "config/java_build_tools.json").read_text())
    for entry in jars:
        if hashlib.sha256((a.java_tools / entry["name"]).read_bytes()).hexdigest() != entry["sha256"]:
            p.error("Compiler/tool checksum mismatch: " + entry["name"])
    patch = ROOT / "patch"
    patch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="toi-dex-") as scratch:
        scratch = Path(scratch)
        smali, classes = scratch / "smali", scratch / "classes"
        classes.mkdir()
        cp = str(a.java_tools.resolve() / "*")
        run(a.java, "-cp", cp, "org.jf.baksmali.Main", "disassemble", a.original_dex, "--api", "24", "-o", smali)
        target = smali / "com/guigugame/guigubahuangoverseas/OverrideActivity.smali"
        expected = json.loads((ROOT / "integration/activity_patch_manifest.json").read_text())
        original = target.read_bytes()
        if hashlib.sha256(original).hexdigest() != expected["original_sha256"]:
            raise ValueError("Unexpected authoritative Activity disassembly")
        diff = (ROOT / "integration/OverrideActivity.smali.patch").read_text()
        additions = "\n".join(line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")) + "\n"
        patched = original + additions.encode()
        if hashlib.sha256(patched).hexdigest() != expected["patched_sha256"]:
            raise ValueError("Lifecycle patch is not reproducible")
        target.write_bytes(patched)
        run(a.java, "-cp", cp, "org.jf.smali.Main", "assemble", smali, "--api", "24", "-o", patch / "classes.dex")
        sources = sorted((ROOT / "android/bridge/src/main/java").rglob("*.java"))
        run(a.java, "-jar", a.java_tools / "ecj-3.38.0.jar", "-source", "1.8", "-target", "1.8", "-proc:none",
            "-classpath", a.android_jar, "-d", classes, *sources)
        output = scratch / "dex"
        output.mkdir()
        run(a.java, "-cp", a.java_tools / "r8-8.7.18.jar", "com.android.tools.r8.D8", "--min-api", "23",
            "--lib", a.android_jar, "--output", output, *sorted(classes.rglob("*.class")))
        (patch / "toimodmenu.dex").write_bytes((output / "classes.dex").read_bytes())
    print("Built patch/classes.dex and patch/toimodmenu.dex; these are not a signed APK")
