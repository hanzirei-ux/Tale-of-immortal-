#!/usr/bin/env python3
"""Apply newly compiled helpers to a recognized v0.2 or v0.3.0 APK.

Leaves the game's primary classes.dex and other assets unchanged. No signing.
For the user's original LiteAPK, first integrate v0.2 using its own patch tool.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from apply_to_apk import aligned_info, check_alignment, SIGNATURE
OLD_MAIN='f87577df61d4f9a18f942b2fa6f594c790a209ee61af8e13625041f84692c4ea'
OLD_HELPER='422aca4048036aed977b42bff202711ff42473338ef052778e64df89a56ee43e'
OLD_NATIVE='d70ce2a1bddb304afacae883bb2ce8a95fe6aaa3da47aea382b23712bd9d5385'
V030_NATIVE='3f5b118cebad5a9517e837e830ef12fc9be5d7659c64bcfb29a9eee63b7ec842'
V030_HELPER='58d83b11105cb758f2f7d9cfc1cf5a877e704824b1dab549d3b795c02e3d9c39'
def sha(data):return hashlib.sha256(data).hexdigest()
def apply(apk,components,output):
    apk,components,output=map(Path,(apk,components,output))
    if apk.resolve()==output.resolve() or output.exists():raise ValueError('Output must be a new file')
    with zipfile.ZipFile(components) as updated:
        for line in updated.read('SHA256SUMS.txt').decode('utf-8').splitlines():
            digest,name=line.split('  ',1)
            if sha(updated.read(name))!=digest:raise ValueError('Compiled component checksum mismatch: '+name)
        dex=updated.read('APK_ROOT/classes2.dex');lib=updated.read('APK_ROOT/lib/arm64-v8a/libtoimodmenu.so')
        with zipfile.ZipFile(apk) as source:
            names=source.namelist()
            if len(names)!=len(set(names)):raise ValueError('Duplicate archive paths')
            if sha(source.read('classes.dex'))!=OLD_MAIN:raise ValueError('Unexpected primary DEX; not v0.2 baseline')
            recognized={OLD_NATIVE:OLD_HELPER,V030_NATIVE:V030_HELPER}
            native_hash=sha(source.read('lib/arm64-v8a/libtoimodmenu.so'))
            if native_hash not in recognized:raise ValueError('Old native library mismatched; expected a known v0.2 or v0.3.0 pair')
            expected_helper=recognized[native_hash]
            candidates=[n for n in names if n.startswith('classes') and n.endswith('.dex') and n!='classes.dex' and sha(source.read(n))==expected_helper]
            if len(candidates)!=1:raise ValueError('Cannot uniquely identify previous helper DEX matching the installed native version')
            helper=candidates[0]
            replacements={helper:dex,'lib/arm64-v8a/libtoimodmenu.so':lib}
            try:
                with zipfile.ZipFile(output,'w',allowZip64=True) as target:
                    target.comment=source.comment
                    for entry in source.infolist():
                        if SIGNATURE.match(entry.filename):continue
                        payload=replacements.get(entry.filename)
                        if payload is None:payload=source.read(entry.filename)
                        method=zipfile.ZIP_STORED if entry.filename.endswith('.so') else entry.compress_type
                        info=aligned_info(entry.filename,target.fp.tell(),method,entry)
                        target.writestr(info,payload)
                check_alignment(output)
            except Exception:
                output.unlink(missing_ok=True)
                raise
            print('Updated',helper,'and libtoimodmenu.so. UNSIGNED APK:',output)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('v02_apk',type=Path);p.add_argument('new_compiled_zip',type=Path);p.add_argument('output_unsigned_apk',type=Path)
    a=p.parse_args()
    try:apply(a.v02_apk,a.new_compiled_zip,a.output_unsigned_apk)
    except Exception as e:sys.exit(str(e))
