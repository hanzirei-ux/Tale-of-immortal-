#include "control_gateway.hpp"
#include "json_utils.hpp"
#include <cmath>
namespace toi {
const char* hookName(HookId h){
    static constexpr const char* names[]{"UnityFrame","DynInt","DynFloat","AddHP","AddMP","PlayerDie","PlayerInit","PlayerDestroy","AddExp","AddFixExp","CultivationSpot","ManualTrain","ManualExp","Cooldown","Shot"};
    auto i=static_cast<uint32_t>(h);return i<static_cast<uint32_t>(HookId::Count)?names[i]:"UnknownHook";
}
uint64_t requiredHooks(uint32_t id){
    const auto hi=hookBit(HookId::DynInt),hf=hookBit(HookId::DynFloat),hp=hookBit(HookId::Hp),mp=hookBit(HookId::Mp),exp=hookBit(HookId::Exp),fix=hookBit(HookId::FixExp),martial=hookBit(HookId::ManualExp);
    switch(static_cast<Control>(id)){
    case Control::GodMode:return hp|hookBit(HookId::Die);
    case Control::HpLock:return hp|hi;
    case Control::EnergyLock:return mp|hi;
    case Control::AllDamage:case Control::MartialDamage:case Control::SpiritualDamage:case Control::SkillDamage:case Control::UltimateDamage:case Control::CritDamage:return hp;
    case Control::Defense:case Control::MartialResistance:case Control::SpiritualResistance:case Control::CritChance:case Control::CritResistance:case Control::MovementSpeed:return hi|hf;
    case Control::AttackSpeed:return hi|hf|hookBit(HookId::Shot);
    case Control::Cooldown:return hookBit(HookId::Cooldown);
    case Control::EnergyCost:return mp;
    case Control::AllExp:return exp|fix;
    case Control::SpotExp:return exp|fix|hookBit(HookId::Spot);
    case Control::ManualExp:return martial|hookBit(HookId::ManualTrain);
    case Control::SkillExp:return martial;
    default:return 0;
    }
}
uint64_t capabilitiesFromHooks(uint64_t installed){uint64_t result=0;for(uint32_t i=0;i<PlayerControlCount;++i){auto need=requiredHooks(i);if(need&&(installed&need)==need)result|=uint64_t(1)<<i;}return result;}
std::string requiredHookNames(uint32_t id){std::string s;auto need=requiredHooks(id);for(uint32_t i=0;i<static_cast<uint32_t>(HookId::Count);++i)if(need&(uint64_t(1)<<i)){if(!s.empty())s+=" + ";s+=hookName(static_cast<HookId>(i));}return s.empty()?"No adapter mapped":s;}
ControlReply applyControlRequest(PolicyStore& policy,const ControlReadiness& state,int id,const std::string& key,bool on,double value){
    ControlReply r;r.id=id;r.key=key;r.requestedEnabled=on;r.requestedValue=value;r.initialized=state.initialized&&!state.failed;r.playerLoaded=state.playerLoaded;r.generation=state.generation;r.installed=state.installedHooks;
    auto spec=id>=0?controlSpec(static_cast<uint32_t>(id)):nullptr;
    auto reject=[&](const char* code,const std::string& detail){r.code=code;r.detail=detail;return r;};
    if(!spec)return reject("CONTROL_ID_MISMATCH","Unknown native control ID");
    r.minimum=spec->minimum;r.maximum=spec->maximum;r.requirements=requiredHooks(static_cast<uint32_t>(id));r.capability=(state.capabilities&(uint64_t(1)<<id))!=0;
    auto before=policy.snapshot().values[size_t(id)];r.enabled=before.enabled;r.value=before.value;
    if(key!=spec->key)return reject("CONTROL_ID_MISMATCH","Java key does not match native ID: expected "+std::string(spec->key));
    if(!std::isfinite(value))return reject("INVALID_VALUE","Value must be finite");
    if(value<spec->minimum||value>spec->maximum)return reject("OUT_OF_RANGE","Requested value is outside the native allowed range");
    // A valid OFF request must remain possible during scene changes or lost capability.
    if(on){
        if(!r.initialized)return reject("NOT_INITIALIZED",state.failed?"Native runtime failed; inspect hook diagnostics":"Native initialization is not complete");
        if(!state.playerLoaded)return reject("PLAYER_NOT_LOADED","Load a player save before enabling this modifier");
        if(!r.capability){
            if(r.requirements&&(state.installedHooks&r.requirements)!=r.requirements)return reject("HOOK_UNAVAILABLE","Required hook installation failed or is pending: "+requiredHookNames(uint32_t(id)));
            return reject("CAPABILITY_DISABLED","Native capability bit is disabled; this is not an input range error");
        }
    }
    if(!policy.set(uint32_t(id),on,value))return reject("NATIVE_REJECTED","Native policy rejected a prevalidated request");
    auto observed=policy.snapshot().values[size_t(id)];r.enabled=observed.enabled;r.value=observed.value;
    if(observed.enabled!=on||observed.value!=value)return reject("NATIVE_REJECTED","Native state changed before readback; inspect current state");
    r.code="APPLIED";r.detail=on?(id>=18?"Player EXP policy accepted and read back; next matching EXP event uses it":state.combatBound?"Policy accepted and read back; gameplay effect still requires device verification":"Policy accepted and read back; combat modifiers wait for the current player's combat binding"):"Runtime control disabled and read back";
    return r;
}
std::string controlReplyJson(const ControlReply& r){
    return "{\"request_id\":"+std::to_string(r.requestId)+",\"generation\":"+std::to_string(r.generation)+",\"control_id\":"+std::to_string(r.id)+",\"key\":"+jsonString(r.key)+",\"result\":"+jsonString(r.code)+",\"detail\":"+jsonString(r.detail)+",\"requested_enabled\":"+jsonBool(r.requestedEnabled)+",\"requested_value\":"+jsonNumber(r.requestedValue)+",\"minimum\":"+jsonNumber(r.minimum)+",\"maximum\":"+jsonNumber(r.maximum)+",\"capability\":"+jsonBool(r.capability)+",\"initialized\":"+jsonBool(r.initialized)+",\"player_loaded\":"+jsonBool(r.playerLoaded)+",\"enabled\":"+jsonBool(r.enabled)+",\"value\":"+jsonNumber(r.value)+",\"required_hooks\":"+jsonString(requiredHookNames(uint32_t(r.id)))+",\"required_mask\":"+jsonString(std::to_string(r.requirements))+",\"installed_mask\":"+jsonString(std::to_string(r.installed))+"}";
}
}
