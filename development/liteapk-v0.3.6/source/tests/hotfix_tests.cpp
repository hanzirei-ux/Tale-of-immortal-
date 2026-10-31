#include "control_gateway.hpp"
#include "localization_cache.hpp"
#include "managed_access.hpp"
#include "catalog_utils.hpp"
#include <cstring>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <vector>
namespace {
int checks=0;
void check(bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);}
void localization(){
    toi::LocalizationCache cache;std::map<std::string,int> calls;
    auto resolve=[&](const std::string& key,int id){return cache.resolve(key,id,[&](int language)->toi::TextLookup{
        ++calls[key+":"+std::to_string(language)];
        if(key=="item_name1041161"||key=="item_name1041162")return {toi::LookupState::Missing,"",""};
        if(key=="pill_cn"&&language==0)return {toi::LookupState::Found,"药丸",""};
        if(key=="manual_en"&&language==2)return {toi::LookupState::Found,"Crescent Manual",""};
        if(key=="material_current"&&language==-1)return {toi::LookupState::Found,"Crescent Herb",""};
        if(key=="recipe_traditional"&&language==1)return {toi::LookupState::Found,"丹方",""};
        return {toi::LookupState::Missing,"",""};
    });};
    struct Item {int id,type;bool recipe;toi::CatalogName name;};
    std::vector<Item> items;
    for(auto row:{std::pair<const char*,int>{"item_name1041161",3},{"item_name1041162",1},{"pill_cn",1},{"manual_en",2},{"material_current",5},{"recipe_traditional",6}}){
        int id=1041161+int(items.size());auto name=resolve(row.first,id);check(!name.failed,"Missing key must not abort indexing");items.push_back({id,row.second,std::strcmp(row.first,"recipe_traditional")==0,std::move(name)});
    }
    check(items.size()==6,"Catalog continues after both exact reported missing keys");
    check(items[0].name.display=="item_name1041161"&&items[1].name.display=="item_name1041162","Actual internal keys retained for missing names");
    check(items[0].name.fallback&&items[1].name.fallback,"Missing entries use explicit fallback");
    check(items[2].name.display=="药丸","English/current missing falls back to Chinese");
    check(items[3].name.display=="Crescent Manual","English alias fallback");
    check(items[4].name.display=="Crescent Herb","Current language is preferred");
    check(items[5].name.display=="丹方","Other available language fallback");
    check(cache.fallbackItems()==2&&cache.missingKeys()>=2,"Missing/fallback diagnostics counted");
    check(cache.summary().find("item_name1041161")!=std::string::npos&&cache.summary().find("item_name1041162")!=std::string::npos,"Exact missing keys available in diagnostics");
    auto before=calls;resolve("item_name1041161",1041161);resolve("item_name1041162",1041162);check(before==calls,"Missing language lookups are memoized, not thrown repeatedly");
    auto count=[&](int filter){int n=0;for(const auto& item:items)if(toi::matchesCatalogCategory(filter,item.type,item.recipe))++n;return n;};
    check(count(-1)==6&&count(1)==2&&count(2)==1&&count(3)==1&&count(5)==1&&count(254)==1,"All required category filters work after fallback");
    check(toi::matchRank(items[0].name.display,std::to_string(items[0].id),"1041161")>=0,"Missing-name item remains searchable by real ID");
    check(toi::matchRank(items[3].name.display,"1","cReS")==0&&toi::matchRank(items[4].name.display,"2","Cres")==0,"Autocomplete still matches resolved names case-insensitively");
    check(toi::matchRank("Great Crescent","3","cres")==1,"Prefix remains ranked before substring");
    auto fatal=cache.resolve("broken",99,[](int)->toi::TextLookup{return {toi::LookupState::Fatal,"","NullReferenceException in localization"};});
    check(fatal.failed&&fatal.error.find("NullReferenceException")!=std::string::npos,"Unexpected managed exceptions are not suppressed");
    auto recovered=cache.resolve("broken",99,[](int)->toi::TextLookup{return {toi::LookupState::Found,"Recovered name",""};});check(!recovered.failed,"Fatal lookup is not permanently memoized");
    auto empty=cache.resolve("",99,[](int)->toi::TextLookup{throw std::runtime_error("Should not invoke empty key");});check(empty.display=="#99"&&!empty.failed,"Empty name still retains real ID without unsafe lookup");
}
uint64_t oldV02Mask(uint64_t hooks){
    using H=toi::HookId;auto has=[&](H h){return (hooks&toi::hookBit(h))!=0;};uint64_t mask=0;auto cap=[&](int i,bool yes){if(yes)mask|=uint64_t(1)<<i;};
    bool hi=has(H::DynInt),hf=has(H::DynFloat),hp=has(H::Hp),mp=has(H::Mp),die=has(H::Die),exp=has(H::Exp),fix=has(H::FixExp),spot=has(H::Spot),manual=has(H::ManualTrain),martial=has(H::ManualExp),cd=has(H::Cooldown),shot=has(H::Shot);
    cap(0,hp&&die);cap(1,hp&&hi);cap(2,mp&&hi);for(int i:{3,4,5,6,7,12})cap(i,hp);for(int i:{8,9,10,11,13,15})cap(i,hi&&hf);cap(14,hi&&hf&&shot);cap(16,cd);cap(17,mp);cap(18,exp&&fix);cap(19,exp&&fix&&spot);cap(20,martial&&manual);cap(21,martial);return mask;
}
void controls(){
    for(uint64_t bits=0;bits<(uint64_t(1)<<15);++bits)check(toi::capabilitiesFromHooks(bits)==oldV02Mask(bits),"Capability requirements must exactly preserve v0.2 for every hook combination");
    toi::PolicyStore store;toi::ControlReadiness state{true,false,true,true,(uint64_t(1)<<22)-1,(uint64_t(1)<<15)-1,7};
    auto defense=toi::applyControlRequest(store,state,8,"all_defense",true,16);
    check(defense.code=="APPLIED"&&defense.enabled&&defense.value==16,"Valid Defense x16 accepted and read back");
    auto invalid=toi::applyControlRequest(store,state,5,"spiritual_damage",true,150);
    check(invalid.code=="OUT_OF_RANGE"&&invalid.minimum==.1&&invalid.maximum==100&&!store.snapshot().values[5].enabled,"Spiritual x150 is range rejection, not hook failure");
    auto valid=toi::applyControlRequest(store,state,5,"spiritual_damage",true,2);
    check(valid.code=="APPLIED"&&valid.value==2,"Valid Spiritual x2 accepted with its hook installed");
    check(toi::controlReplyJson(valid).find("OUT_OF_RANGE")==std::string::npos,"Successful reply contains no stale prior failure");
    check(toi::controlReplyJson(defense).find("\"control_id\":8")!=std::string::npos&&toi::controlReplyJson(invalid).find("\"control_id\":5")!=std::string::npos,"Each result carries exact current control ID");
    auto missing=state;missing.installedHooks&=~toi::hookBit(toi::HookId::DynFloat);missing.capabilities=toi::capabilitiesFromHooks(missing.installedHooks);
    check(toi::applyControlRequest(store,missing,8,"all_defense",true,16).code=="HOOK_UNAVAILABLE","Missing DynFloat reported as unavailable hook");
    auto disabled=state;disabled.capabilities&=~(uint64_t(1)<<8);check(toi::applyControlRequest(store,disabled,8,"all_defense",true,16).code=="CAPABILITY_DISABLED","Disabled capability distinguished from hook failure");
    auto uninitialized=state;uninitialized.initialized=false;check(toi::applyControlRequest(store,uninitialized,8,"all_defense",true,16).code=="NOT_INITIALIZED","Initialization gating");
    auto unloaded=state;unloaded.playerLoaded=false;check(toi::applyControlRequest(store,unloaded,8,"all_defense",true,16).code=="PLAYER_NOT_LOADED","Player ownership gating");
    check(toi::applyControlRequest(store,state,8,"spiritual_damage",true,16).code=="CONTROL_ID_MISMATCH","Java/native key mismatch rejected");
    check(toi::applyControlRequest(store,state,64,"bad",true,16).code=="CONTROL_ID_MISMATCH"&&toi::applyControlRequest(store,state,-1,"bad",true,1).code=="CONTROL_ID_MISMATCH","Invalid IDs cannot shift capability mask or write policy");
    auto nan=toi::applyControlRequest(store,state,8,"all_defense",true,std::numeric_limits<double>::quiet_NaN());check(nan.code=="INVALID_VALUE"&&toi::controlReplyJson(nan).find("\"requested_value\":null")!=std::string::npos,"Nonfinite values rejected with valid JSON");
    check(toi::applyControlRequest(store,unloaded,8,"all_defense",false,16).code=="APPLIED"&&!store.snapshot().values[8].enabled,"OFF remains possible across scene transitions");
    auto waiting=state;waiting.combatBound=false;check(toi::applyControlRequest(store,waiting,8,"all_defense",true,16).detail.find("wait")!=std::string::npos,"Policy acceptance does not imply a combat binding");
    auto policy=store.snapshot();toi::Scope scope{1,7,0};auto event=toi::Event{toi::Kind::Defense,toi::Category::General,1,7,0,100,0,false};
    check(toi::evaluatePolicy(policy,scope,event).value==1600,"Canonical player Defense policy uses accepted value");event.actor=2;check(toi::evaluatePolicy(policy,scope,event).value==100,"NPC Defense remains unchanged");
    for(int id=0;id<22;++id){auto spec=toi::controlSpec(uint32_t(id));check(toi::applyControlRequest(store,state,id,spec->key,true,id<3?1:spec->neutral).code=="APPLIED","All 22 supported control IDs accept valid policy values");}
}
struct FakeClass {const char* name;const char* ns;};
struct FakeMethod {FakeClass* owner;const char* name;};
FakeClass localizer{"ConfLocalText",""},keyException{"KeyNotFoundException","System.Collections.Generic"},nullException{"NullReferenceException","System"};
FakeClass* activeException=&keyException;int formatted=0;
void managedMissing(){
    toi::ManagedApi a{};a.runtime_invoke=[](const void*,void*,void**,void** ex)->void*{*ex=activeException;return nullptr;};a.object_get_class=[](void* o)->void*{return o;};
    a.class_get_name=[](void* c){return static_cast<FakeClass*>(c)->name;};a.class_get_namespace=[](void* c){return static_cast<FakeClass*>(c)->ns;};a.method_get_class=[](const void* m)->void*{return static_cast<const FakeMethod*>(m)->owner;};a.method_get_name=[](const void* m){return static_cast<const FakeMethod*>(m)->name;};
    a.format_exception=[](void*,char* dst,int n){++formatted;std::strncpy(dst,"managed error",size_t(n)-1);};a.format_stack_trace=[](void*,char* dst,int n){std::strncpy(dst,"useful stack",size_t(n)-1);};
    toi::ManagedAccess m;m.api=&a;m.context="Catalog item #1041161 key=item_name1041161";FakeMethod method{&localizer,"GetText"};
    m.invoke(&method,nullptr,nullptr,true);check(m.failed&&formatted==0,"Expected localization key misses avoid repeated stack formatting");check(m.consumeMissingLocalization()&&!m.failed,"Exact localization KeyNotFound is recoverable");
    activeException=&nullException;m.invoke(&method,nullptr,nullptr,true);check(!m.consumeMissingLocalization()&&m.failed&&formatted==1&&m.error.find("useful stack")!=std::string::npos,"NullReference keeps full managed error context");
    FakeClass other{"OtherLookup",""};method.owner=&other;activeException=&keyException;m.invoke(&method,nullptr,nullptr,true);check(!m.consumeMissingLocalization(),"Non-localization KeyNotFound is not swallowed");
    FakeClass custom{"KeyNotFoundException","CustomGame"};method.owner=&localizer;activeException=&custom;m.invoke(&method,nullptr,nullptr,true);check(!m.consumeMissingLocalization(),"Same exception name in another namespace is not swallowed");
}
}
int main(){try{localization();controls();managedMissing();std::cout<<"PASS v0.3.1: "<<checks<<" host checks; no device/gameplay verification\n";return 0;}catch(const std::exception& e){std::cerr<<"FAIL v0.3.1 after "<<checks<<" checks: "<<e.what()<<'\n';return 1;}}
