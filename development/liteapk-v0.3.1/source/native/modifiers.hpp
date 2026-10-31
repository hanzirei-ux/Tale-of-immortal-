#pragma once
#include <array>
#include <cstdint>
#include <mutex>
#include <string>

namespace toi {
// Shared validation/math policy; Android adapters are in game_runtime.cpp.
enum class Control : uint32_t {
    GodMode, HpLock, EnergyLock, AllDamage, MartialDamage, SpiritualDamage,
    SkillDamage, UltimateDamage, Defense, MartialResistance, SpiritualResistance,
    CritChance, CritDamage, CritResistance, AttackSpeed, MovementSpeed,
    Cooldown, EnergyCost, AllExp, SpotExp, ManualExp, SkillExp,
    CultivationSpeed, BreakthroughChance, CraftCost, CraftSpeed, CraftSuccess,
    ArtifactDamage, ArtifactCooldown, Count
};
enum class Combine : uint32_t { CategoryOverride, MultiplyGlobalAndCategory };
struct ControlSpec { const char* key;double minimum,maximum,neutral; };
struct Setting { bool enabled{};double value{}; };
struct Policy {
    std::array<Setting,static_cast<size_t>(Control::Count)> values;
    Combine combine{Combine::CategoryOverride};
};
const ControlSpec* controlSpec(uint32_t id);
Policy defaults();
class PolicyStore {
public:
    bool set(uint32_t id,bool enabled,double value);
    bool setCombine(uint32_t mode);
    Policy snapshot() const;
    void reset();
private:
    mutable std::mutex mutex_;
    Policy policy_{defaults()};
};
enum class Kind : uint32_t {
    OutgoingDamage,IncomingDamage,HpResource,EnergyResource,Defense,
    MartialResistance,SpiritualResistance,CritChance,CritDamage,CritResistance,
    AttackSpeed,MovementSpeed,Cooldown,EnergyCost,Exp,CultivationSpeed,
    BreakthroughChance,CraftCost,CraftSpeed,CraftSuccess,ArtifactDamage,ArtifactCooldown
};
enum class Category : uint32_t { General,Martial,Spiritual,Skill,Ultimate,Spot,Manual,SkillExp };
struct Scope {
    uintptr_t player{};
    uint64_t worldGeneration{};
    uintptr_t selectedArtifact{};
};
struct Event {
    Kind kind{};Category category{};
    uintptr_t actor{};
    uint64_t worldGeneration{};
    uintptr_t artifact{};
    double value{},maximum{};
    bool alreadyApplied{};
};
struct Evaluated { double value;bool applied; };
Evaluated evaluatePolicy(const Policy&,const Scope&,const Event&);
enum class Edit : uint32_t { Set,Add,Subtract,Multiply };
// Calculates an edit only; it does not read/write a character or a save.
bool calculateStatEdit(double current,Edit operation,double operand,
                       double minimum,double maximum,bool integer,double& output);
} // namespace toi
