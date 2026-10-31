#include "modifiers.hpp"
#include <algorithm>
#include <cmath>

namespace toi {
namespace {
constexpr ControlSpec specs[]{
    {"god_mode",0,1,0},{"unlimited_hp",0,1,0},{"unlimited_energy",0,1,0},
    {"all_damage",.1,100,1},{"martial_damage",.1,100,1},{"spiritual_damage",.1,100,1},
    {"skill_damage",.1,100,1},{"ultimate_damage",.1,100,1},{"all_defense",.1,100,1},
    {"martial_resistance",.1,100,1},{"spiritual_resistance",.1,100,1},
    {"critical_rating",0,100,0},{"critical_damage",.1,100,1},
    {"critical_resistance_rating",0,100,0},{"attack_speed",1,10,1},
    {"movement_speed",1,10,1},{"skill_cooldown",0,1,1},{"energy_consumption",0,1,1},
    {"global_exp",1,100,1},{"cultivation_spot_exp",1,100,1},{"manual_exp",1,100,1},
    {"skill_exp",1,100,1},{"cultivation_speed",1,100,1},{"breakthrough_chance_percent",0,100,0},
    {"crafting_material_cost",0,1,1},{"crafting_speed",1,100,1},
    {"crafting_success_percent",0,100,0},{"artifact_skill_damage",.1,100,1},
    {"artifact_skill_cooldown",0,1,1}
};
static_assert(sizeof(specs)/sizeof(specs[0])==static_cast<size_t>(Control::Count),"Control table mismatch");
const Setting& setting(const Policy& p,Control c) {return p.values[static_cast<size_t>(c)];}
double factor(const Policy& p,Control c) {auto& s=setting(p,c);return s.enabled?s.value:1;}
double combined(const Policy& p,Control global,Control category) {
    auto& s=setting(p,category);
    if(!s.enabled) return factor(p,global);
    return p.combine==Combine::CategoryOverride?s.value:std::min(100.0,factor(p,global)*s.value);
}
}
const ControlSpec* controlSpec(uint32_t id) {return id<static_cast<uint32_t>(Control::Count)?&specs[id]:nullptr;}
Policy defaults() {
    Policy p;
    for(size_t i=0;i<p.values.size();++i) p.values[i]={false,specs[i].neutral};
    return p;
}
bool PolicyStore::set(uint32_t id,bool enabled,double value) {
    auto s=controlSpec(id);
    if(!s || !std::isfinite(value) || value<s->minimum || value>s->maximum) return false;
    std::lock_guard<std::mutex> lock(mutex_);
    policy_.values[id]={enabled,value};return true;
}
bool PolicyStore::setCombine(uint32_t mode) {
    if(mode>static_cast<uint32_t>(Combine::MultiplyGlobalAndCategory)) return false;
    std::lock_guard<std::mutex> lock(mutex_);policy_.combine=static_cast<Combine>(mode);return true;
}
Policy PolicyStore::snapshot() const {std::lock_guard<std::mutex> lock(mutex_);return policy_;}
void PolicyStore::reset() {std::lock_guard<std::mutex> lock(mutex_);policy_=defaults();}
Evaluated evaluatePolicy(const Policy& p,const Scope& scope,const Event& e) {
    if(!scope.player || !scope.worldGeneration || e.actor!=scope.player ||
       e.worldGeneration!=scope.worldGeneration || e.alreadyApplied ||
       !std::isfinite(e.value) || e.value<0) return {e.value,false};
    double output=e.value;Control selected{};bool simple=true,absolute=false;
    switch(e.kind) {
    case Kind::OutgoingDamage:
        simple=false;
        switch(e.category) {
        case Category::Martial:output*=combined(p,Control::AllDamage,Control::MartialDamage);break;
        case Category::Spiritual:output*=combined(p,Control::AllDamage,Control::SpiritualDamage);break;
        case Category::Skill:output*=combined(p,Control::AllDamage,Control::SkillDamage);break;
        case Category::Ultimate:output*=combined(p,Control::AllDamage,Control::UltimateDamage);break;
        default:output*=factor(p,Control::AllDamage);break;
        }break;
    case Kind::IncomingDamage:
        simple=false;
        if(setting(p,Control::GodMode).enabled) output=0;
        break;
    case Kind::HpResource:
    case Kind::EnergyResource:
        simple=false;
        if(setting(p,e.kind==Kind::HpResource?Control::HpLock:Control::EnergyLock).enabled &&
           std::isfinite(e.maximum) && e.maximum>=0) output=e.maximum;
        break;
    case Kind::Defense:selected=Control::Defense;break;
    case Kind::MartialResistance:selected=Control::MartialResistance;break;
    case Kind::SpiritualResistance:selected=Control::SpiritualResistance;break;
    case Kind::CritChance:selected=Control::CritChance;absolute=true;break;
    case Kind::CritDamage:selected=Control::CritDamage;break;
    case Kind::CritResistance:selected=Control::CritResistance;absolute=true;break;
    case Kind::AttackSpeed:selected=Control::AttackSpeed;break;
    case Kind::MovementSpeed:selected=Control::MovementSpeed;break;
    case Kind::Cooldown:selected=Control::Cooldown;break;
    case Kind::EnergyCost:
        simple=false;
        output=setting(p,Control::EnergyLock).enabled?0:e.value*factor(p,Control::EnergyCost);
        break;
    case Kind::Exp:
        simple=false;
        switch(e.category) {
        case Category::Spot:output*=combined(p,Control::AllExp,Control::SpotExp);break;
        case Category::Manual:output*=combined(p,Control::AllExp,Control::ManualExp);break;
        case Category::SkillExp:output*=combined(p,Control::AllExp,Control::SkillExp);break;
        default:output*=factor(p,Control::AllExp);break;
        }break;
    case Kind::CultivationSpeed:selected=Control::CultivationSpeed;break;
    case Kind::BreakthroughChance:selected=Control::BreakthroughChance;absolute=true;break;
    case Kind::CraftCost:selected=Control::CraftCost;break;
    case Kind::CraftSpeed:selected=Control::CraftSpeed;break;
    case Kind::CraftSuccess:selected=Control::CraftSuccess;absolute=true;break;
    case Kind::ArtifactDamage:
    case Kind::ArtifactCooldown:
        if(!scope.selectedArtifact || e.artifact!=scope.selectedArtifact) return {e.value,false};
        selected=e.kind==Kind::ArtifactDamage?Control::ArtifactDamage:Control::ArtifactCooldown;
        break;
    default:return {e.value,false};
    }
    if(simple) {
        auto& s=setting(p,selected);
        if(!s.enabled) return {e.value,false};
        output=absolute?s.value:e.value*s.value;
    }
    if(!std::isfinite(output)) return {e.value,false};
    return {output,output!=e.value};
}
bool calculateStatEdit(double current,Edit operation,double operand,
                       double minimum,double maximum,bool integer,double& output) {
    if(!std::isfinite(current)||!std::isfinite(operand)||!std::isfinite(minimum)||
       !std::isfinite(maximum)||minimum>maximum) return false;
    long double v{};
    switch(operation) {
    case Edit::Set:v=operand;break;
    case Edit::Add:v=static_cast<long double>(current)+operand;break;
    case Edit::Subtract:v=static_cast<long double>(current)-operand;break;
    case Edit::Multiply:v=static_cast<long double>(current)*operand;break;
    default:return false;
    }
    if(!std::isfinite(v)||v<minimum||v>maximum) return false;
    if(integer) v=std::trunc(v);
    output=static_cast<double>(v);return true;
}
} // namespace toi
