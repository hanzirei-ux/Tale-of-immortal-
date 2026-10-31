#!/usr/bin/env python3
"""Package only the verified newly compiled helper DEX + ARM64 SO."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD_DEX='422aca4048036aed977b42bff202711ff42473338ef052778e64df89a56ee43e'
OLD_SO='d70ce2a1bddb304afacae883bb2ce8a95fe6aaa3da47aea382b23712bd9d5385'
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'out/TaleOfImmortal_ModMenu_v0.3.0_Binary_Patch.zip');a=p.parse_args()
    files={'APK_ROOT/classes2.dex':ROOT/'out/toimodmenu.dex','APK_ROOT/lib/arm64-v8a/libtoimodmenu.so':ROOT/'patch/lib/arm64-v8a/libtoimodmenu.so'}
    report=json.loads((ROOT/'evidence/artifact_verification_v03.json').read_text());api=json.loads((ROOT/'evidence/jni_api_verification.json').read_text())
    hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()}
    if hashes['APK_ROOT/classes2.dex'] in [OLD_DEX] or hashes['APK_ROOT/lib/arm64-v8a/libtoimodmenu.so'] in [OLD_SO]:raise SystemExit('Refusing old v0.2 binaries')
    if hashes['APK_ROOT/classes2.dex']!=report['helper_dex']['sha256'] or hashes['APK_ROOT/lib/arm64-v8a/libtoimodmenu.so']!=report['native']['sha256']:raise SystemExit('Binaries changed since validation; rerun verifier')
    if api['api_version']!=3 or api['native_method_count']!=17:raise SystemExit('JNI pair not verified')
    if not (ROOT/'evidence/editor_target_verification.json').is_file():raise SystemExit('Missing current baseline target verification')
    files.update({'README_ID.txt':ROOT/'README_ID.txt','TEST_CHECKLIST.txt':ROOT/'TEST_CHECKLIST.txt','THIRD_PARTY_NOTICES.txt':ROOT/'THIRD_PARTY_NOTICES.txt'})
    checksums=''.join(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+name+'\n' for name,path in files.items())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,path in files.items():z.write(path,name)
        z.writestr('SHA256SUMS.txt',checksums)
    with zipfile.ZipFile(a.output) as z:
        if z.testzip():raise SystemExit('ZIP CRC failed')
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            digest,name=line.split('  ',1)
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise SystemExit('ZIP component digest mismatch')
    print(json.dumps({'file':str(a.output),'bytes':a.output.stat().st_size,'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'status':'COMPILED — NOT DEVICE TESTED','files':hashes},indent=2))
if __name__=='__main__':main()
