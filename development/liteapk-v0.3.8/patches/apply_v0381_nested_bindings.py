#!/usr/bin/env python3
"""Verified LiteAPK v0.3.8 -> v0.3.8.1 nested IL2CPP binding repair.

Applied only AFTER verifying and restoring the private v0.3.7/v0.3.8 source.
Strict text guards prevent applying this to an unknown version.
Does not modify Item ID allowlists, NPC/Sect controls or save data.
"""
from pathlib import Path
import argparse

def one(data, old, new, label, expected=1):
    got=data.count(old)
    if got!=expected:
        raise RuntimeError(f"{label}: expected {expected} occurrences, found {got}; refusing patch")
    return data.replace(old,new)

def main(root):
    native=root/"native"
    files={name:(native/name).read_text() for name in
           ("managed_access.hpp","managed_access.cpp","game_runtime.cpp","item_creation.cpp")}
    files["managed_access.hpp"]=one(files["managed_access.hpp"],
        "    ManagedClass* (*class_get_parent)(ManagedClass*);",
        "    ManagedClass* (*class_get_parent)(ManagedClass*);ManagedClass* (*class_get_nested_types)(ManagedClass*,void**);",
        "IL2CPP nested API")
    files["managed_access.cpp"]=one(files["managed_access.cpp"],
        'ManagedClass* ManagedAccess::klass(const char* name){return api->class_from_name(image,"",name);}',
        '''ManagedClass* ManagedAccess::klass(const char* name){
    if(!api||!api->class_from_name||!name)return nullptr;
    if(std::strcmp(name,"DataProps.PropsData")!=0&&std::strcmp(name,"DataProps.PropsArtifact")!=0)
        return api->class_from_name(image,"",name);
    if(!api->class_get_nested_types||!api->class_get_name)return nullptr;
    auto parent=api->class_from_name(image,"","DataProps");
    if(!parent)return nullptr;
    auto expected=std::strrchr(name,'.');
    if(!expected)return nullptr;
    ++expected;
    void* iterator=nullptr;
    ManagedClass* found=nullptr;
    while(auto nested=api->class_get_nested_types(parent,&iterator)){
        auto actual=api->class_get_name(nested);
        if(actual&&std::strcmp(actual,expected)==0){
            if(found&&found!=nested)return nullptr;
            found=nested;
        }
    }
    return found;
}''', "nested-class lookup")
    files["game_runtime.cpp"]=one(files["game_runtime.cpp"],
        "    LOAD(class_get_parent);LOAD(field_get_type);LOAD(field_get_flags);LOAD(field_static_get_value);",
        "    LOAD(class_get_parent);LOAD(class_get_nested_types);LOAD(field_get_type);LOAD(field_get_flags);LOAD(field_static_get_value);",
        "nested export loading")
    item=files["item_creation.cpp"]
    for old,new,label,n in (
        ('{"PropsData","System.Boolean"}','{"DataProps.PropsData","System.Boolean"}',"reward object signature",1),
        ('{"NewProps",0x060085a4,"PropsData"','{"NewProps",0x060085a4,"DataProps.PropsData"',"new props result",1),
        ('{"GetProps",0x060084fe,"PropsData"','{"GetProps",0x060084fe,"DataProps.PropsData"',"get props result",1),
        ('{"AddProps",0x060084f6,"$ref",{"PropsData"}','{"AddProps",0x060084f6,"$ref",{"DataProps.PropsData"}',"add props signature",1),
        ('{"RewardItem",0x06015a90,"RewardItemData"','{"RewardItem",0x06015a90,"WorldUnitData.RewardItemData"',"manual receipt result",1),
        ('m.klass("PropsData")','m.klass("DataProps.PropsData")',"nested PropsData class",2),
        ('m.klass("PropsArtifact")','m.klass("DataProps.PropsArtifact")',"nested PropsArtifact class",1),
        ('m.setObjectField(wrapper,"data",prop,"PropsData")','m.setObjectField(wrapper,"data",prop,"DataProps.PropsData")',"nested Artifact data field",1),
        ('return blocked(m,"Native item reward method unavailable");',
         'return blocked(m,devil?"DataProps.AddProps(DataProps.PropsData) binding unavailable":"WorldUnitData.RewardPropItem(Int32,Int32,Bool) binding unavailable");',
         "item reward diagnostics",1),
    ):
        item=one(item,old,new,label,n)
    item=one(item,
        'if(!cls||!ctor||!factory||!reward||!m.api->object_new)return blocked(m,"Checked native manual generator unavailable");',
        '''if(!cls)return blocked(m,"Missing RandomGetRewardData class");
    if(!ctor)return blocked(m,"Missing RandomGetRewardData constructor token 0600a568");
    if(!factory)return blocked(m,"Missing RewardTool.GetReward token 0600a577");
    if(!reward)return blocked(m,"Missing WorldUnitData.RewardItem token 06015a90 / nested RewardItemData return");
    if(!m.api->object_new)return blocked(m,"IL2CPP object allocation API unavailable");''',"manual granular diagnostics")
    item=one(item,
        'if(!cls||!ctor||!init||!setRates||!setGrade||!reward||!make||!m.api->object_new)return blocked(m,"Checked native Artifact factory unavailable");',
        '''if(!cls)return blocked(m,"Missing nested DataProps.PropsArtifact class");
    if(!ctor)return blocked(m,"Missing PropsArtifact constructor token 06008563");
    if(!init)return blocked(m,"Missing PropsDataBase.Init token 0600850b");
    if(!setRates)return blocked(m,"Missing PropsArtifact.SetAttrrRate token 06008560");
    if(!setGrade)return blocked(m,"Missing PropsArtifact.set_grade token 06008544");
    if(!reward)return blocked(m,"Missing WorldUnitData.RewardPropItem(PropsData,Bool) token 06015a8c");
    if(!make)return blocked(m,"Missing nested DataProps.PropsData.NewProps token 060085a4");
    if(!m.api->object_new)return blocked(m,"IL2CPP object allocation API unavailable");''',
        "artifact granular diagnostics")
    files["item_creation.cpp"]=item
    for name,new_data in files.items():
        (native/name).write_text(new_data)
    print("Applied guarded v0.3.8.1 nested type repair; no Item Policy or NPC/Sect source touched.")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    main(ap.parse_args().source)
