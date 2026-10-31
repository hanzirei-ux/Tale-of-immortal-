#!/usr/bin/env python3
"""Package a newly compiled, matching v0.3.1 helper pair only."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import source_revision
ROOT=Path(__file__).resolve().parents[1]
OLD_DEX={'422aca4048036aed977b42bff202711ff42473338ef052778e64df89a56ee43e','58d83b11105cb758f2f7d9cfc1cf5a877e704824b1dab549d3b795c02e3d9c39'}
OLD_SO={'d70ce2a1bddb304afacae883bb2ce8a95fe6aaa3da47aea382b23712bd9d5385','3f5b118cebad5a9517e837e830ef12fc9be5d7659c64bcfb29a9eee63b7ec842'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'out/TaleOfImmortal_ModMenu_v0.3.1_StabilityHotfix_BinaryPatch.zip');a=p.parse_args()
    paths={'APK_ROOT/classes2.dex':ROOT/'out/toimodmenu.dex','APK_ROOT/lib/arm64-v8a/libtoimodmenu.so':ROOT/'patch/lib/arm64-v8a/libtoimodmenu.so'}
    report=json.loads((ROOT/'evidence/artifact_verification_v031.json').read_text());api=json.loads((ROOT/'evidence/jni_api_verification_v031.json').read_text())
    revision=source_revision.digest();records={k:json.loads((ROOT/f'out/{k}_build_v031.json').read_text()) for k in ['native','dex']}
    hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in paths.items()}
    for kind,name in [('dex','APK_ROOT/classes2.dex'),('native','APK_ROOT/lib/arm64-v8a/libtoimodmenu.so')]:
        if records[kind]['source_revision']!=revision or records[kind]['artifact_sha256']!=hashes[name]:raise SystemExit('Build record/source revision mismatch: '+kind)
    if hashes['APK_ROOT/classes2.dex'] in OLD_DEX or hashes['APK_ROOT/lib/arm64-v8a/libtoimodmenu.so'] in OLD_SO:raise SystemExit('Refusing old renamed components')
    if report['helper_dex']['sha256']!=hashes['APK_ROOT/classes2.dex'] or report['native']['sha256']!=hashes['APK_ROOT/lib/arm64-v8a/libtoimodmenu.so']:raise SystemExit('Components changed after verification')
    if api['api_version']!=4 or api['native_method_count']!=19:raise SystemExit('Incorrect JNI pair')
    for name in ['README_ID.txt','CHANGELOG.txt','TEST_CHECKLIST.txt','THIRD_PARTY_NOTICES.txt']:paths[name]=ROOT/name
    checksums=''.join(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+name+'\n' for name,path in paths.items())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,path in paths.items():z.write(path,name)
        z.writestr('SHA256SUMS.txt',checksums)
    with zipfile.ZipFile(a.output) as z:
        if z.testzip():raise SystemExit('ZIP CRC failed')
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            digest,name=line.split('  ',1)
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise SystemExit('ZIP checksum failed')
    summary=dict(file=a.output.name,bytes=a.output.stat().st_size,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),source_revision=revision,protocol=4,native_methods=19,status='COMPILED — NOT DEVICE TESTED',signed_apk_produced=False,components={name:dict(sha256=hashes[name],bytes=paths[name].stat().st_size) for name in hashes})
    (ROOT/'evidence/binary_patch_manifest_v031.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
