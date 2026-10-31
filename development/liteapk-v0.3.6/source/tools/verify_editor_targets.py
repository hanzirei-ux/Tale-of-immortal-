#!/usr/bin/env python3
"""Read-only checks for this exact LiteAPK binary/metadata and editor method specs.

Runtime code uses public IL2CPP metadata APIs. The pinned registration location is
used only for this host-side type audit, after both complete SHA-256 checks.
It is not a hook address and is never written to the game.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
import metadata_probe as probe

def verify(library,metadata,source):
    raw=library.read_bytes();data=metadata.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099':raise ValueError('Library hash mismatch')
    if hashlib.sha256(data).hexdigest()!=probe.BASELINE_HASH:raise ValueError('Metadata hash mismatch')
    md=probe.MetadataV31(data);types=list(struct.iter_unpack('<16I8H2I',md.types))
    with library.open('rb') as f:
        elf=ELFFile(f);segs=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD'];rel={}
        exports={s.name for s in elf.get_section_by_name('.dynsym').iter_symbols()}
        for sec in elf.iter_sections():
            if sec['sh_type']=='SHT_RELA':
                for t in sec.iter_relocations():
                    if t['r_info_type']==1027:rel[t['r_offset']]=t['r_addend']
    def off(a,n=8):
        for s in segs:
            d=a-s['p_vaddr']
            if 0<=d and d+n<=s['p_filesz']:return s['p_offset']+d
        raise ValueError('Registration pointer outside file mapping')
    def u64(a):return struct.unpack_from('<Q',raw,off(a))[0]
    def ptr(a):return rel.get(a,u64(a))
    reg=0x7ea2688
    if u64(reg+48)!=55858 or u64(reg+80)!=len(types):raise ValueError('Registration layout mismatch')
    table=ptr(reg+56)
    primitives={1:'System.Void',2:'System.Boolean',3:'System.Char',4:'System.SByte',5:'System.Byte',6:'System.Int16',7:'System.UInt16',8:'System.Int32',9:'System.UInt32',10:'System.Int64',11:'System.UInt64',12:'System.Single',13:'System.Double',14:'System.String',24:'System.IntPtr',25:'System.UIntPtr',28:'System.Object'}
    def typename(ix,depth=0):
        if not 0<=ix<55858 or depth>8:raise ValueError('Type index/depth bound')
        a=ptr(table+ix*8);d,b=struct.unpack_from('<QI',raw,off(a,12));code=(b>>16)&255
        if code in primitives:return primitives[code]
        if code in (17,18):
            t=types[d];name=md.string(t[0]);ns=md.string(t[1]);parent=t[3]
            return typename(parent,depth+1)+'.'+name if parent!=0xffffffff else (ns+'.' if ns else '')+name
        if code in (21,29):return '$ref'
        raise ValueError('Unsupported type code '+str(code))
    probe.TARGETS.update(['g','ConfMgr','ConfLocalText','ConfItemPropsBase','ConfMakePillFormulaBase','DataProps','DataObjectData','UnitDataProps','SchoolData','MapBuildSchool','WorldUnitData','DynInt','UIPlayerBagExtend','UIPlayerPorp','UISwitchPlayerBagPorp','UIImmortalStore','UIMgr'])
    records={int(x['token'],16):x for x in md.report()['targets'] if x['image']=='Assembly-CSharp.dll'}
    checks=[]
    pattern=r'const M (\w+)\{"([^"]+)",0x([0-9a-f]+),"([^"]+)",\{([^}]*)\}(,true)?\};'
    for x in re.finditer(pattern,source.read_text()):
        label,name,token,ret,pars,static=x.groups();row=records[int(token,16)];actual=typename(row['return_type_index']);pa=[typename(p['type_index']) for p in row['parameters']]
        expected=re.findall(r'"([^"]+)"',pars)
        ok=row['method']==name and (ret==actual or ret=='$ref' and actual not in primitives.values()) and pa==expected and row['static']==bool(static)
        checks.append(dict(label=label,type=row['type'],method=name,token='0x'+token,return_type=actual,parameters=pa,static=row['static'],match=ok))
    if len(checks)<25 or not all(x['match'] for x in checks):raise ValueError('Editor signature mismatch: '+str(checks))
    defaults={i:(t,d) for i,t,d in struct.iter_unpack('<Iii',md.table(16,12))}
    constants=[]
    for owner,name,expected in [('PropsIDType','Money',10001),('PropsIDType','SchoolMoney',10011),('PropsIDType','CityToken',10041),('UIImmortalStore','TokenPropID',10051)]:
        found=[]
        for t in types:
            if md.string(t[0])!=owner:continue
            for fi in range(t[8],t[8]+t[18]):
                field=struct.unpack_from('<IIi',md.fields,fi*12)
                if md.string(field[0])!=name:continue
                ti,di=defaults[fi]
                if typename(ti)!='System.Int32' or di<0:raise ValueError('Currency constant type mismatch')
                at=md.h[18]+di;first=data[at]
                # v31 stores default Int32 values as compressed unsigned zig-zag.
                if first<0x80:encoded=first
                elif first<0xc0:encoded=((first&0x3f)<<8)|data[at+1]
                elif first<0xe0:encoded=((first&0x1f)<<24)|int.from_bytes(data[at+1:at+4],'big')
                else:raise ValueError('Unsupported compressed currency literal')
                if encoded&1:raise ValueError('Currency identifier is negative')
                value=encoded>>1;found.append(value)
        if found!=[expected]:raise ValueError('Currency identifier mismatch '+owner+'.'+name+str(found))
        constants.append(dict(type=owner,name=name,value=found[0]))
    required=['class_get_namespace','class_get_parent','field_get_type','field_get_flags','field_static_get_value','method_get_token','method_get_flags','method_get_return_type','method_get_class','type_get_name','free','object_unbox','format_exception','format_stack_trace']
    if any('il2cpp_'+name not in exports for name in required):raise ValueError('Missing required native API')
    # Independently recheck the observed no-op capacity setter in this hash.
    if raw[off(0x5655280,4):off(0x5655280,4)+4]!=bytes.fromhex('c0035fd6'):raise ValueError('Capacity setter changed')
    return dict(status='STATIC VERIFIED',device_tested=False,method_specs=checks,currency_constants=constants,required_apis=required,prop_grid_base_setter='ret (no-op)',baseline_sha256=hashlib.sha256(raw).hexdigest(),metadata_sha256=hashlib.sha256(data).hexdigest())
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('library',type=Path);p.add_argument('metadata',type=Path);p.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]/'native/game_editors.cpp');p.add_argument('--report',type=Path);a=p.parse_args()
    report=verify(a.library,a.metadata,a.source);text=json.dumps(report,indent=2)+'\n'
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(text)
    print('STATIC VERIFIED:',len(report['method_specs']),'method signatures,',len(report['currency_constants']),'currency IDs, native exports and capacity setter')
