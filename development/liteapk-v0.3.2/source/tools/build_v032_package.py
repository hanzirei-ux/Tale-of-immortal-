#!/usr/bin/env python3
"""Package only the newly compiled helper DEX; the exact v0.3.1 SO stays installed."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import source_revision
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'out/TaleOfImmortal_ModMenu_v0.3.2_ReadOnlyCatalogExporter_BinaryPatch.zip');a=p.parse_args()
    report=json.loads((ROOT/'evidence/artifact_verification_v032.json').read_text())
    record=json.loads((ROOT/'out/dex_build_v032.json').read_text());reuse=json.loads((ROOT/'config/v031_reuse_hashes.json').read_text())
    dex=ROOT/'out/toimodmenu.dex';revision=source_revision.digest()
    if record['source_revision']!=revision or record['artifact_sha256']!=sha(dex) or report['helper_dex']['sha256']!=sha(dex):raise ValueError('Stale source/DEX/verification')
    if sha(dex)=='3047bb58ffe729365604d8142471fdf013e47c537cee48a5508fd4763001e7a3':raise ValueError('Old v0.3.1 DEX')
    if report['native']['sha256']!=reuse['native_sha256'] or report['native_recompiled'] or report['native_in_patch']:raise ValueError('Native reuse contract mismatch')
    api=json.loads((ROOT/'evidence/jni_api_verification_v032.json').read_text())
    if api['api_version']!=4 or api['native_method_count']!=19:raise ValueError('JNI protocol mismatch')
    paths={'APK_ROOT/classes2.dex':dex}
    for name in ['README_ID.txt','CHANGELOG.txt','TEST_CHECKLIST.txt','THIRD_PARTY_NOTICES.txt']:paths[name]=ROOT/name
    sums=''.join(sha(path)+'  '+name+'\n' for name,path in paths.items())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,path in paths.items():z.write(path,name)
        z.writestr('SHA256SUMS.txt',sums)
    with zipfile.ZipFile(a.output) as z:
        assert z.testzip() is None
        assert not any(n.endswith(('.so','.dat','.ab','.apk')) for n in z.namelist())
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            digest,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==digest
    manifest=dict(version='0.3.2',file=a.output.name,bytes=a.output.stat().st_size,sha256=sha(a.output),source_revision=revision,status='COMPILED — NOT DEVICE TESTED',dex_sha256=sha(dex),dex_bytes=dex.stat().st_size,java_native_protocol=4,jni_methods=19,native_in_patch=False,native_required_sha256=reuse['native_sha256'],native_origin_commit=reuse['v031_commit'],signed_apk_produced=False,device_tested=False)
    (ROOT/'evidence/binary_patch_manifest_v032.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
