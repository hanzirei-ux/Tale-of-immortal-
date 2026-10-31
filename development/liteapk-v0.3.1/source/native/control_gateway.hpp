#pragma once
#include "modifiers.hpp"
#include <cstdint>
#include <string>
namespace toi {
enum class HookId:uint32_t {Frame,DynInt,DynFloat,Hp,Mp,Die,PlayerInit,PlayerDestroy,Exp,FixExp,Spot,ManualTrain,ManualExp,Cooldown,Shot,Count};
constexpr size_t PlayerControlCount=22;
constexpr uint64_t hookBit(HookId h){return uint64_t(1)<<static_cast<uint32_t>(h);}
const char* hookName(HookId);
uint64_t requiredHooks(uint32_t control);
uint64_t capabilitiesFromHooks(uint64_t installed);
std::string requiredHookNames(uint32_t control);
struct ControlReadiness {bool initialized{},failed{},playerLoaded{},combatBound{};uint64_t capabilities{},installedHooks{},generation{};};
struct ControlReply {
    uint64_t requestId{},generation{};
    int id{};std::string key,code="NOT_APPLIED",detail;
    bool requestedEnabled{},enabled{},capability{},initialized{},playerLoaded{};
    double requestedValue{},value{},minimum{},maximum{};
    uint64_t requirements{},installed{};
};
ControlReply applyControlRequest(PolicyStore&,const ControlReadiness&,int id,const std::string& key,bool enabled,double value);
std::string controlReplyJson(const ControlReply&);
}
