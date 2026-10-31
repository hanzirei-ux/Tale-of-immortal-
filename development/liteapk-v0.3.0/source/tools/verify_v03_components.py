#!/usr/bin/env python3
"""Verify freshly built v0.3 DEX/native components without proprietary game files."""
import argparse,hashlib,json,re
from pathlib import Path
from elftools.elf.elffile import ELFFile
from verify_artifacts import dex_info
ROOT=Path(__file__).resolve().parents[1]
def verify():
    dex=ROOT/'out/toimodmenu.dex';lib=ROOT/'patch/lib/arm64-v8a/libtoimodmenu.so';info=dex_info(dex)
    if not {'Lorg/npc/toibridge/NativeBridge;','Lorg/npc/toibridge/ModMenu;'}.issubset(info['classes']):raise ValueError('Missing integrated helper classes')
    if any(not c.startswith('Lorg/npc/toibridge/') for c in info['classes']):raise ValueError('Unexpected game/third-party class in helper DEX')
    ctype={'void':'V','jboolean':'Z','jint':'I','jlong':'J','jdouble':'D','jstring':'Ljava/lang/String;'};jni=(ROOT/'native/jni.cpp').read_text();pairs=[]
    for ret,name,params in re.findall(r'JNIEXPORT\s+(\w+)\s+JNICALL\s+Java_org_npc_toibridge_NativeBridge_(\w+)\(([^)]*)\)',jni):
        args=params.split(',')[2:];desc='('+''.join(ctype[x.strip().split()[0]] for x in args)+')'+ctype[ret]
        if 'Lorg/npc/toibridge/NativeBridge;->'+name+desc not in info['native_methods']:raise ValueError('JNI descriptor mismatch '+name)
        pairs.append(dict(name=name,descriptor=desc,match=True))
    if len(pairs)!=len(info['native_methods']) or len(pairs)!=17:raise ValueError('JNI API count mismatch')
    with lib.open('rb') as f:
        e=ELFFile(f);segments=list(e.iter_segments())
        if e.elfclass!=64 or e['e_machine']!='EM_AARCH64' or e['e_type']!='ET_DYN':raise ValueError('Wrong ELF/ABI')
        loads=[s for s in segments if s['p_type']=='PT_LOAD']
        if not loads or any(s['p_align']<16384 for s in loads):raise ValueError('Missing 16 KiB LOAD alignment')
        if not any(s['p_type']=='PT_GNU_RELRO' for s in segments):raise ValueError('Missing RELRO')
        if any(s['p_type']=='PT_GNU_STACK' and s['p_flags']&1 for s in segments):raise ValueError('Executable stack')
        tags=list(e.get_section_by_name('.dynamic').iter_tags());needed=[t.needed for t in tags if t.entry.d_tag=='DT_NEEDED']
        if set(needed)-{'libdl.so','liblog.so','libm.so','libc.so'}:raise ValueError('Unexpected shared dependency')
        symbols={s.name for s in e.get_section_by_name('.dynsym').iter_symbols() if s['st_shndx']!='SHN_UNDEF'}
        required={'JNI_OnLoad','toi_bridge_pump','toi_mod_abi_version'}|{'Java_org_npc_toibridge_NativeBridge_'+p['name'] for p in pairs}
        if required-symbols:raise ValueError('Missing native exports '+str(required-symbols))
    compact={k:v for k,v in info.items() if k not in ['classes','methods','native_methods']}
    report=dict(status='COMPILED — NOT DEVICE TESTED',device_tested=False,helper_dex=compact,native=dict(sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),size=lib.stat().st_size,abi='arm64-v8a',needed=needed,jni_methods_exported=17,load_alignment=16384,relro=True,executable_stack=False),game_profile_sites_verified=None,note='This component-only check does not repeat the private baseline/primary DEX audit.')
    api=dict(status='STATIC VERIFIED',api_version=3,native_method_count=17,pairs=pairs)
    return report,api
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,default=ROOT/'evidence/artifact_verification_v03.json');a=p.parse_args();report,api=verify()
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');(ROOT/'evidence/jni_api_verification.json').write_text(json.dumps(api,indent=2)+'\n')
    print('PASS: helper DEX, ARM64 ELF, 16 KiB alignment, system dependencies and all 17 JNI descriptors. NOT DEVICE TESTED.')
