#!/usr/bin/env python3
"""Generate verified baseline RVAs and 16-byte prologue fingerprints; no old RVAs."""
import argparse,hashlib,json
from pathlib import Path
from elftools.elf.elffile import ELFFile
EXPECTED='c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099'
SELECT={
 'UnityFrame':('UnityEngine.UnitySynchronizationContext$$ExecuteTasks',None),
 'GetWorld':('g$$get_world',None),'GetConf':('g$$get_conf',None),
 'PlayerInit':('UnitCtrlPlayer$$InitData','WorldUnitData_o* unitData'),
 'PlayerDestroy':('UnitCtrlPlayer$$Destroy',None),'PlayerDie':('UnitCtrlPlayer$$Die',None),
 'AddHP':('UnitDataBase$$AddHP',None),'AddMP':('UnitDataBase$$AddMP',None),
 'DataUnit':('UnitDataBase$$get_unit',None),'HitAttacker':('MartialTool.HitData$$get_attackUnit',None),
 'DynInt':('DynInt$$get_value',None),'DynFloat':('DynInt$$get_valueFloat',None),
 'DynBase':('DynInt$$get_baseValue',None),'DynSet':('DynInt$$set_baseValue',None),
 'AddExp':('DataUnit.PropertyData$$AddExp',None),'AddFixExp':('DataUnit.PropertyData$$AddFixExp',None),
 'SpotExp':('UnitActionGridGetExp$$OnCreate',None),'ManualTrain':('UnitActionMartialTrain$$OnCreate',None),
 'ManualExp':('DataUnit.UnitInfoData$$AddMartialExp',None),
 'Cooldown':('SkillDataAttack$$get_cdTime',None),'Shot':('SkillDataBase$$get_shotCD',None),
 'SkillOwner':('SkillBase$$get_unit',None),'DataSkill':('SkillDataBase$$get_skill',None),
 'ItemConf':('ConfMgr$$get_itemProps',None),'ItemList':('ConfItemPropsBase$$get_allConfList',None),
 'ItemGet':('ConfItemPropsBase$$GetItem',None),
 'RewardItem':('WorldUnitData$$RewardPropItem','int32_t id, int32_t count'),
 'GridCount':('DataUnit.UnitDataProps$$GetGridCurNum','__this, const MethodInfo*'),
}
def generate(lib,script,output):
 raw=Path(lib).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=EXPECTED:raise ValueError('Library fingerprint mismatch')
 methods=json.loads(Path(script).read_text())['ScriptMethod'];report={}
 with open(lib,'rb') as f:
  elf=ELFFile(f);segs=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
  for key,(name,signature) in SELECT.items():
   matches=[x for x in methods if x['Name']==name and (signature is None or signature in x['Signature'])]
   if not matches and key=='UnityFrame':matches=[x for x in methods if x['Name'].endswith('UnitySynchronizationContext$$ExecuteTasks')]
   if len(matches)!=1:raise ValueError((key,name,len(matches)))
   m=matches[0];a=m['Address'];seg=next(s for s in segs if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz'] and s['p_flags']&1)
   off=a-seg['p_vaddr']+seg['p_offset'];report[key]={**m,'FileOffset':off,'Prologue16':raw[off:off+16].hex()}
 header='#pragma once\n#include <cstdint>\nnamespace toi::profile {\nstruct Site {uintptr_t rva;unsigned char prologue[16];const char* name;};\n'
 for key,m in report.items():
  header+='inline constexpr Site '+key+'{'+hex(m['Address'])+', {'+','.join(hex(x) for x in bytes.fromhex(m['Prologue16']))+'}, "'+m['Name']+'"};\n'
 header+='}\n';Path(output).write_text(header)
 Path(output).with_suffix('.json').write_text(json.dumps({'baseline_sha256':EXPECTED,'methods':report},indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('library');p.add_argument('script_json');p.add_argument('output');a=p.parse_args();generate(a.library,a.script_json,a.output)
