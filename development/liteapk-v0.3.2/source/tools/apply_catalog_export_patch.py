#!/usr/bin/env python3
"""Apply the DEX-only exporter to a recognized private v0.3.1 APK. Output is UNSIGNED."""
import argparse,hashlib,zipfile
from pathlib import Path
from apply_to_apk import aligned_info,check_alignment,SIGNATURE
MAIN='f87577df61d4f9a18f942b2fa6f594c790a209ee61af8e13625041f84692c4ea'
HELPER='3047bb58ffe729365604d8142471fdf013e47c537cee48a5508fd4763001e7a3'
NATIVE='ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729'
def sha(data):return hashlib.sha256(data).hexdigest()
def apply(apk,patch,output):
    apk,patch,output=map(Path,(apk,patch,output))
    if output.exists() or output.resolve()==apk.resolve():raise ValueError('Choose a new output file; original APK must be retained')
    with zipfile.ZipFile(patch) as z:
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate patch paths')
        checks=dict(line.split('  ',1)[::-1] for line in z.read('SHA256SUMS.txt').decode().splitlines())
        name='APK_ROOT/classes2.dex';dex=z.read(name)
        if checks.get(name)!=sha(dex) or not dex.startswith(b'dex\n'):raise ValueError('New helper DEX checksum/header mismatch')
        for name,digest in checks.items():
            if sha(z.read(name))!=digest:raise ValueError('Patch checksum mismatch: '+name)
    with zipfile.ZipFile(apk) as source:
        names=source.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate APK paths')
        if sha(source.read('classes.dex'))!=MAIN:raise ValueError('Primary DEX is not the retained v0.3.1/v0.2 integration')
        if sha(source.read('lib/arm64-v8a/libtoimodmenu.so'))!=NATIVE:raise ValueError('Install the working v0.3.1 native component first; this patch contains no SO')
        candidates=[n for n in names if n.startswith('classes') and n.endswith('.dex') and n!='classes.dex' and sha(source.read(n))==HELPER]
        if len(candidates)!=1:raise ValueError('Cannot uniquely locate the original v0.3.1 helper DEX')
        helper=candidates[0]
        try:
            with zipfile.ZipFile(output,'w',allowZip64=True) as target:
                target.comment=source.comment
                for entry in source.infolist():
                    if SIGNATURE.match(entry.filename):continue
                    data=dex if entry.filename==helper else source.read(entry.filename)
                    method=zipfile.ZIP_STORED if entry.filename.endswith('.so') else entry.compress_type
                    target.writestr(aligned_info(entry.filename,target.fp.tell(),method,entry),data)
            check_alignment(output)
        except Exception:
            output.unlink(missing_ok=True);raise
    print('Updated only',helper,'; original native and game payloads retained. UNSIGNED:',output)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input_v031_apk',type=Path);p.add_argument('v032_patch_zip',type=Path);p.add_argument('output_unsigned_apk',type=Path);a=p.parse_args();apply(a.input_v031_apk,a.v032_patch_zip,a.output_unsigned_apk)
