#!/usr/bin/env python3
"""Build only the changed helper DEX; reuse the existing v0.2 patched classes.dex.

Requires Java 17, Android SDK platform android.jar and the pinned compiler JARs.
Does not redistribute any game classes or assets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import source_revision
ROOT = Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--java-tools',required=True,type=Path)
    p.add_argument('--android-jar',required=True,type=Path)
    p.add_argument('--java',default='java')
    args=p.parse_args()
    revision=source_revision.digest()
    if not args.android_jar.is_file():p.error('Android SDK android.jar not found')
    tools=json.loads((ROOT/'config/java_build_tools.json').read_text())
    for entry in tools:
        f=args.java_tools/entry['name']
        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=entry['sha256']:
            p.error('Missing or mismatched compiler: '+entry['name'])
    sources=sorted((ROOT/'android/bridge/src/main/java').rglob('*.java'))
    if not sources:p.error('No Java sources')
    with tempfile.TemporaryDirectory(prefix='toi-v036-dex-') as tmp:
        classes=Path(tmp)/'classes';classes.mkdir()
        output=Path(tmp)/'dex';output.mkdir()
        def run(parts):subprocess.run([str(x) for x in parts],check=True)
        run([args.java,'-jar',args.java_tools/'ecj-3.38.0.jar','-source','1.8','-target','1.8',
             '-proc:none','-classpath',args.android_jar,'-d',classes,*sources])
        run([args.java,'-cp',args.java_tools/'r8-8.7.18.jar','com.android.tools.r8.D8',
             '--min-api','23','--lib',args.android_jar,'--output',output,*sorted(classes.rglob('*.class'))])
        dex=(output/'classes.dex').read_bytes()
        if not dex.startswith(b'dex\n'):raise RuntimeError('DEX output invalid')
        target=ROOT/'out'/'toimodmenu.dex';target.parent.mkdir(exist_ok=True)
        target.write_bytes(dex)
        if revision!=source_revision.digest():raise RuntimeError('Source changed during DEX build; rebuild helper DEX')
        source_revision.record('dex',target,ROOT/'out/dex_build_v036.json')
        print('Built',target,'bytes=',len(dex),'sha256=',hashlib.sha256(dex).hexdigest())
if __name__=='__main__':main()
