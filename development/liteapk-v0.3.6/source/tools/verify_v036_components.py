#!/usr/bin/env python3
"""Check actual compiled v0.3.6 DEX against the unchanged v0.3.1/2 JNI/native ABI."""
import argparse,hashlib,json
from pathlib import Path
import source_revision
from verify_v031_components import verify
from verify_artifacts import dex_info
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--v032-dex',type=Path,required=True);a=p.parse_args()
    report,api=verify();current=dex_info(ROOT/'out/toimodmenu.dex');previous=dex_info(a.v032_dex)
    if previous['sha256']!='7e1f65e069785ab12ed89479c7e74cff6ad8fbcdc21351622354dea6b67a9ac9':raise ValueError('Not the actual v0.3.2 helper DEX')
    if previous['native_methods']!=current['native_methods']:raise ValueError('JNI descriptor drift')
    for name in ['FullCatalogExport','CatalogDefinitions','ReadOnlyCatalogExport','CatalogDocumentFragment','CatalogExportGuard']:
        if 'Lorg/npc/toibridge/'+name+';' not in current['classes']:raise ValueError('Compiled collector class missing: '+name)
    for name in ['ModMenu;->startFullCatalogExport()V','FullCatalogExport;->beforeCommit()V','FullCatalogExport;->itemJson(ILjava/lang/String;Ljava/lang/String;Ljava/lang/String;J)Ljava/lang/String;']:
        if 'Lorg/npc/toibridge/'+name not in current['methods']:raise ValueError('Compiled full collector entry point missing: '+name)
    dex=(ROOT/'out/toimodmenu.dex').read_bytes()
    for text in [b'Export Full Catalog',b'COMPLETE_SUPPORTED_SCOPE',b'BLOCKED_NATIVE',b'REFERENCE_ID_GAP',b'VERIFIED_METADATA']:
        if text not in dex:raise ValueError('Required implementation string not compiled: '+repr(text))
    reuse=json.loads((ROOT/'config/v031_reuse_hashes.json').read_text())
    if report['native']['sha256']!=reuse['native_sha256']:raise ValueError('The proven native SO changed')
    for name,digest in reuse['unchanged_source'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('Native/JNI source changed: '+name)
    record=json.loads((ROOT/'out/dex_build_v036.json').read_text())
    if record['source_revision']!=source_revision.digest() or record['artifact_sha256']!=current['sha256']:raise ValueError('Stale build/source record')
    report.update(version='0.3.6',source_revision=record['source_revision'],new_native_hooks=0,native_recompiled=False,native_in_patch=False,v032_native_declarations_identical=True,full_native_tables_available=False,baseline_reference_ids=3284)
    (ROOT/'evidence/artifact_verification_v036.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'evidence/jni_api_verification_v036.json').write_text(json.dumps(api,indent=2)+'\n')
    print('PASS: new DEX full-schema implementation, actual v0.3.2 JNI parity, unchanged ARM64 SO, source revision. No device test; extended native tables remain BLOCKED_NATIVE.')
