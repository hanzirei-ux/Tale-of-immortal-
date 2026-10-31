#!/usr/bin/env python3
"""Extract specific IL2CPP metadata v31 type/method associations; no rewriting."""
import struct,csv,json,hashlib,sys
from pathlib import Path
B=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/tales_audit/global-metadata.dat').read_bytes()
V=struct.unpack_from('<64I',B)
assert (V[0],V[1])==(0xFAB11BAF,31)
str_data=B[V[6]:V[6]+V[7]]
def s(i):
 if not 0<=i<len(str_data):return '<BAD>'
 j=str_data.find(b'\x00',i)
 return str_data[i:j].decode('utf8','replace')
images=[]
assert V[43]%40==0
for i in range(V[43]//40):
 r=struct.unpack_from('<10I',B,V[42]+i*40)
 images.append({'image':s(r[0]),'start':r[2], 'count':r[3]})
# All type defs from metadata by direct index; image lookup via range.
types=[]; x_fmt='<16I8H2I'
assert V[41]%88==0
for i in range(V[41]//88):
 t=struct.unpack_from(x_fmt,B,V[40]+i*88)
 name=s(t[0]);namespace=s(t[1]);image=next((im['image'] for im in images if im['start']<=i<im['start']+im['count']),'<unknown>')
 types.append({'name':name,'namespace':namespace,'type_index':i,'image':image,'method_start':t[9],'method_count':t[16]})
methods=[]
assert V[13]%36==0
for i in range(V[13]//36):
 m=struct.unpack_from('<7I4H',B,V[12]+i*36)
 methods.append({'method_index':i,'name':s(m[0]),'type_index':m[1],'parameter_count':m[10],'token':hex(m[6])})

TARGETS={
'GMCmd', 'GMCmdTool','GMFunc','EditorCommand','UIPlayerGM','UIPlayerGMBase',
'UI_EditorTest1Cmd','UI_EditorTest1Unit','UI_EditorTest1Skill','UI_EditorTest6',
'UI_EditorTest1CmdInfo','UINPCSearch','UIPlayerBagExtend','UIPlayerBagExtendBase',
'ConfMakePillFormula','ConfRuneFormula','UnitActionPropPillFormulaStudy',
'UIPillFormulaView','UIRefinePillFormula','UIRefineElixir','ConfArtifactSpriteTalent',
'ConfArtifactSpriteSkill','PropsArtifact','PropItemDataArtifact',
}
TARGET_METHODS={
'GMFunc':{'UnitGradeUp','npctishengjingjie','doujiInvincible','shuangyupeidianshu','zongmenshuxing'},
'GMCmd':{'CMDCall','Execute','Support','get_cmdDesc','openggm'},
'UI_EditorTest6':{'UpdatePlayerLockHP','UpdatePlayerCD','UpdateMonstAI'},
'UI_EditorTest1Cmd':{'QuickSelectCMD','Init','Update'},
'UIPlayerBagExtend':{'UpdatePropsCount','get_gridCurNum','get_gridMaxNum'},
}
rows=[];all_target_names=[]
for t in types:
 if t['name'] not in TARGETS:continue
 all_target_names.append(t)
 a,b=t['method_start'],t['method_count']
 for m in methods[a:a+b]:
  if m['type_index']!=t['type_index']:continue
  rows.append({'image':t['image'],'type':t['name'],'type_index':t['type_index'], 'method':m['name'], 'method_index':m['method_index'],'parameters':m['parameter_count'],'method_token':m['token']})
p=Path('TaleOfImmortal_IL2CPP_Target_Methods.csv')
with p.open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Types:',len(types),'methods:',len(methods),'images:',len(images),'targets',len(all_target_names),'rows',len(rows))
for t in all_target_names:
 ms=[r for r in rows if r['type']==t['name'] and r['type_index']==t['type_index']]
 selected=[m for m in ms if t['name'] not in TARGET_METHODS or m['method'] in TARGET_METHODS[t['name']]]
 print('TYPE',t['name'],'IMAGE',t['image'],'TYPEINDEX',t['type_index'],'METHODS',len(ms))
 print(' KEY',', '.join(f"{r['method']}({r['parameters']})@{r['method_index']}" for r in selected[:40]))
