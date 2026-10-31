#!/usr/bin/env python3
"""Validate the new DEX against the exact, reused v0.3.1 ARM64 component."""
import argparse,hashlib,json
from pathlib import Path
import source_revision
from verify_v031_components import verify
from verify_artifacts import dex_info
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--v031-dex',type=Path);args=p.parse_args()
    report,api=verify()
    info=dex_info(ROOT/'out/toimodmenu.dex')
    required={'ReadOnlyCatalogExport','CatalogExportGuard','CatalogFileCopy','CatalogDocumentFragment'}
    if not {'Lorg/npc/toibridge/'+name+';' for name in required}.issubset(info['classes']):raise ValueError('Exporter classes missing from compiled DEX')
    methods=['ModMenu;->startReadOnlyCatalogExport()V','ReadOnlyCatalogExport;->acceptPage(Ljava/lang/String;)I','CatalogDocumentFragment;->onActivityResult(IILandroid/content/Intent;)V']
    if any('Lorg/npc/toibridge/'+name not in info['methods'] for name in methods):raise ValueError('Compiled exporter entry point missing')
    if b'Export ALL item IDs (read-only)' not in (ROOT/'out/toimodmenu.dex').read_bytes():raise ValueError('Compiled menu label missing')
    if args.v031_dex:
        old=dex_info(args.v031_dex)
        if old['sha256']!='3047bb58ffe729365604d8142471fdf013e47c537cee48a5508fd4763001e7a3':raise ValueError('Unexpected baseline helper DEX')
        if old['native_methods']!=info['native_methods']:raise ValueError('JNI methods changed relative to actual v0.3.1 DEX')
    reuse=json.loads((ROOT/'config/v031_reuse_hashes.json').read_text())
    if report['native']['sha256']!=reuse['native_sha256']:raise ValueError('Native component is not the unchanged v0.3.1 binary')
    for path,digest in reuse['unchanged_source'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Changed native/JNI source: '+path)
    record=json.loads((ROOT/'out/dex_build_v032.json').read_text())
    if record['source_revision']!=source_revision.digest() or record['artifact_sha256']!=report['helper_dex']['sha256']:raise ValueError('Stale DEX/source record')
    report.update(version='0.3.2',source_revision=record['source_revision'],native_recompiled=False,native_origin_commit=reuse['v031_commit'],native_source_files_unchanged=len(reuse['unchanged_source']),native_in_patch=False,compiled_exporter_classes=sorted(required),compiled_exporter_entrypoints_present=True,v031_dex_native_methods_identical=bool(args.v031_dex))
    (ROOT/'evidence/artifact_verification_v032.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'evidence/jni_api_verification_v032.json').write_text(json.dumps(api,indent=2)+'\n')
    print('PASS: new v0.3.2 DEX, unchanged v0.3.1 ARM64 SO, protocol 4 / 19 JNI descriptors, checksums and source provenance. NOT DEVICE TESTED.')
