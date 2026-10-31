#!/usr/bin/env python3
"""Read-only, hash-pinned schema/enum audit reusing the existing v31 parser/registration.

No config rows or save files are read. Metadata fields describe schemas, not values.
The registration location is the existing host audit mapping, never a hook address.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
import metadata_probe as probe
ROOT=Path(__file__).resolve().parents[1]
LIB_HASH='c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099'
TABLES={
 'ConfItemPropsItem':'items','ConfItemTypeItem':'item_types','ConfItemTypeFixedItem':'item_types',
 'ConfRoleGradeItem':'realms','ConfItemHorseItem':'items','ConfClothItemItem':'items',
 'ConfItemBookItem':'books','ConfItemSkillItem':'manual_templates',
 'ConfBattleSkillBaseItem':'skill_templates','ConfBattleSkillLevelItem':'skill_templates',
 'ConfBattleSkillPrefixNameItem':'skill_templates','ConfBattleSkillPrefixValueItem':'skill_templates',
 'ConfLocalTextItem':'localization','MartialInfoData':'manual_instances',
}
class CheckedMetadata:
 def __init__(self,library,metadata):
  self.raw=library.read_bytes();data=metadata.read_bytes()
  if hashlib.sha256(self.raw).hexdigest()!=LIB_HASH or hashlib.sha256(data).hexdigest()!=probe.BASELINE_HASH:raise ValueError('Mismatched LiteAPK binary/metadata')
  self.md=probe.MetadataV31(data);self.types=list(struct.iter_unpack('<16I8H2I',self.md.types));self.rel={}
  self.images=[(self.md.string(r[0]),r[2],r[3]) for r in struct.iter_unpack('<10I',self.md.images)]
  with library.open('rb') as stream:
   elf=ELFFile(stream);self.segs=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
   for section in elf.iter_sections():
    if section['sh_type']=='SHT_RELA':
     for r in section.iter_relocations():
      if r['r_info_type']==1027:self.rel[r['r_offset']]=r['r_addend']
  reg=0x7ea2688
  if self.u64(reg+48)!=55858 or self.u64(reg+80)!=len(self.types):raise ValueError('Existing registration audit mapping no longer matches')
  self.type_table=self.ptr(reg+56)
 def offset(self,address,size=8):
  for s in self.segs:
   d=address-s['p_vaddr']
   if 0<=d and d+size<=s['p_filesz']:return s['p_offset']+d
  raise ValueError('Metadata type pointer outside file')
 def u64(self,a):return struct.unpack_from('<Q',self.raw,self.offset(a))[0]
 def image(self,index):return next((name for name,start,count in self.images if start<=index<start+count),None)
 def ptr(self,a):return self.rel.get(a,self.u64(a))
 def type_name(self,index):
  if not 0<=index<55858:raise ValueError('Type registration index out of range')
  a=self.ptr(self.type_table+index*8);d,b=struct.unpack_from('<QI',self.raw,self.offset(a,12));code=(b>>16)&255
  primitives={1:'System.Void',2:'System.Boolean',3:'System.Char',4:'System.SByte',5:'System.Byte',6:'System.Int16',7:'System.UInt16',8:'System.Int32',9:'System.UInt32',10:'System.Int64',11:'System.UInt64',12:'System.Single',13:'System.Double',14:'System.String',24:'System.IntPtr',25:'System.UIntPtr',28:'System.Object'}
  if code in primitives:return primitives[code]
  if code in (17,18):
   t=self.types[d];return (self.md.string(t[1])+'.' if self.md.string(t[1]) else '')+self.md.string(t[0])
  return {21:'GENERIC_INSTANCE',29:'ARRAY',15:'POINTER',16:'BYREF'}.get(code,'TYPE_CODE_'+str(code))
 def constants(self,owner):
  defaults={i:(t,d) for i,t,d in struct.iter_unpack('<Iii',self.md.table(16,12))};found=[]
  types=[t for t in self.types if self.md.string(t[0])==owner and not self.md.string(t[1])]
  if len(types)!=1:raise ValueError('Ambiguous enum owner')
  t=types[0]
  for fi in range(t[8],t[8]+t[18]):
   f=struct.unpack_from('<IIi',self.md.fields,fi*12)
   if fi not in defaults:continue
   ti,di=defaults[fi]
   if self.type_name(ti)!='System.Int32' or di<0:raise ValueError('Enum default is not a checked Int32')
   at=self.md.h[18]+di;b=self.md.data[at]
   if b<0x80:encoded=b
   elif b<0xc0:encoded=((b&0x3f)<<8)|self.md.data[at+1]
   elif b<0xe0:encoded=((b&0x1f)<<24)|int.from_bytes(self.md.data[at+1:at+4],'big')
   else:raise ValueError('Unexpected compressed enum literal')
   found.append({'kind':'item_type','id':(encoded>>1)^-(encoded&1),'name':self.md.string(f[0]),'source_table':owner,'status':'VERIFIED_METADATA','field_status':{'id':'VERIFIED_METADATA','name':'VERIFIED_METADATA','source_table':'VERIFIED_METADATA'},'official_scope':'Metadata enum only; relationship to ConfItemProps.type is not verified. Not localized ConfItemType data.'})
  return found
 def contracts(self):
  result=[]
  for ix,t in enumerate(self.types):
   name=self.md.string(t[0])
   if name not in TABLES or self.md.string(t[1]) or t[3]!=0xffffffff or self.image(ix)!='Assembly-CSharp.dll':continue
   fields=[]
   for fi in range(t[8],t[8]+t[18]):
    f=struct.unpack_from('<IIi',self.md.fields,fi*12);fields.append({'name':self.md.string(f[0]),'type':self.type_name(f[1]),'metadata_field_index':fi,'status':'VERIFIED_METADATA','value':None,'value_status':'UNKNOWN'})
   result.append({'kind':'metadata_contract','section':TABLES[name],'owner':name,'image':self.image(ix),'type_index':ix,'fields':fields,'status':'VERIFIED_METADATA','data_values_available':False,'note':'Global type schema only; field definitions are not configuration rows or runtime offsets'})
  if len(result)!=len(TABLES) or {r['owner'] for r in result}!=set(TABLES):raise ValueError('Missing/ambiguous collector schema target')
  return result
def generate(library,metadata,output):
 checked=CheckedMetadata(library,metadata);enums=checked.constants('PropsType');contracts=checked.contracts()
 expected={'Money':0,'Pill':1,'Martial':2,'Equip':3,'Material':5,'Other':6}
 if {x['name']:x['id'] for x in enums}!=expected:raise ValueError('Unexpected PropsType enum; inspect instead of silently remapping')
 audit={'version':'0.3.6','library_sha256':LIB_HASH,'metadata_sha256':probe.BASELINE_HASH,'registration_mapping_reused':True,'item_types':enums,'contracts':contracts,'runtime_rows_collected':False,'native_interface':'protocol 4 catalog: id/display_name/props_type/level only'}
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
 return audit
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('library',type=Path);p.add_argument('metadata',type=Path);p.add_argument('--output',type=Path,default=ROOT/'config/catalog_metadata_v036.json');a=p.parse_args();r=generate(a.library,a.metadata,a.output);print('PASS:',len(r['item_types']),'verified enum entries,',len(r['contracts']),'verified metadata schemas; no config values invented')
