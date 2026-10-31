#!/usr/bin/env python3
"""Read-only compare of the supplied v0.2, GitHub v0.3, and current hotfix source."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def function(text,name):
    pattern=r'\b'+re.escape(name)+r'\([^;]*?\)\s*(?:const\s*)?\{'
    m=re.search(pattern,text,re.S)
    if not m:raise ValueError('Missing function '+name)
    start=m.end()-1;depth=0;i=start
    while i<len(text):
        if text.startswith('//',i):i=text.find('\n',i);continue
        if text.startswith('/*',i):i=text.index('*/',i)+2;continue
        if text[i] in ['"',"'"]:
            quote=text[i];i+=1
            while i<len(text):
                if text[i]=='\\':i+=2;continue
                if text[i]==quote:break
                i+=1
        elif text[i]=='{':depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0:return text[start:i+1]
        i+=1
    raise ValueError('Unbalanced source')
def audit(v02,v030):
    current=(ROOT/'native/game_runtime.cpp').read_text();old=(v02/'native/game_runtime.cpp').read_text();previous=(v030/'native/game_runtime.cpp').read_text()
    hooks=['hookInt','hookFloat','hookInit','hookDestroy','hookDie','hookHP','hookMP','hookExp','hookFixExp','hookSpot','hookManual','hookMartialExp','hookCooldown','hookShot','combinedExp','expFactor']
    combat={n:dict(v02_unchanged=function(old,n)==function(current,n),v030_unchanged=function(previous,n)==function(current,n)) for n in hooks}
    profile={n:(v02/'native'/n).read_bytes()==(ROOT/'native'/n).read_bytes()==(v030/'native'/n).read_bytes() for n in ['baseline_profile.hpp','baseline_profile.json','modifiers.cpp','modifiers.hpp']}
    before=(v030/'native/game_editors.cpp').read_text();after=(ROOT/'native/game_editors.cpp').read_text()
    editors={n:function(before,n)==function(after,n) for n in ['currency','capacity','modifyCapacity','bind','storeBonus','loadBonus','balance','refreshInventory']}
    if not all(v['v02_unchanged'] and v['v030_unchanged'] for v in combat.values()) or not all(profile.values()) or not all(editors.values()):raise ValueError('Unintended gameplay/resource regression: '+str((combat,profile,editors)))
    return dict(status='STATIC VERIFIED',device_tested=False,combat_and_exp_bodies=combat,profile_and_policy=profile,currency_capacity_bodies=editors,combat_binding_change='Data refresh keeps an owner-validated player controller; identity changes still clear it; generation still cancels persistent edits.',finding='The generic v0.3 UI failure was not cleared on success and checkbox rollback could recursively apply. A screenshot alone cannot establish that Defense x16 failed natively.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--v02',type=Path,required=True);p.add_argument('--v030',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();r=audit(a.v02,a.v030);a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,indent=2)+'\n');print('PASS: combat/EXP bodies and profiles match v0.2/v0.3; currency/capacity functions match v0.3')
