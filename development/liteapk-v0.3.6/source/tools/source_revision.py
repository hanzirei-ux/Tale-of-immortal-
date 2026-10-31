#!/usr/bin/env python3
"""Content identity shared by the native and DEX build records (not a game hash)."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(root=ROOT):
    files=[]
    for folder in ['native','android/bridge/src/main/java','config']:
        files.extend(p for p in (root/folder).rglob('*') if p.is_file())
    files.extend(root/p for p in ['CMakeLists.txt','scripts/build_android.sh','tools/build_menu_dex_only.py','tools/source_revision.py'])
    h=hashlib.sha256()
    for p in sorted(files):
        h.update(p.relative_to(root).as_posix().encode()+b'\0');h.update(p.read_bytes());h.update(b'\0')
    return h.hexdigest()
def record(kind,artifact,output):
    artifact=Path(artifact);output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    value=dict(version='0.3.6',kind=kind,source_revision=digest(),artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),bytes=artifact.stat().st_size,device_tested=False)
    output.write_text(json.dumps(value,indent=2)+'\n');return value
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',choices=['native','dex']);p.add_argument('--artifact',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.record:
        if not a.artifact or not a.output:p.error('--artifact and --output required')
        print(json.dumps(record(a.record,a.artifact,a.output)))
    else:print(digest())
