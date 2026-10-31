#include "mod_api.h"
#include "modifiers.hpp"
#ifdef __ANDROID__
#include "game_runtime.hpp"
namespace { auto& policies=toi::runtimePolicyStore(); }
#else
namespace { toi::PolicyStore policies; }
#endif
extern "C" {
uint32_t toi_mod_abi_version() {return 2;}
uint32_t toi_mod_control_count() {return static_cast<uint32_t>(toi::Control::Count);}
const char* toi_mod_control_key(uint32_t id) {auto s=toi::controlSpec(id);return s?s->key:nullptr;}
int toi_mod_set_control(uint32_t id,int enabled,double value) {
    if(enabled!=0 && enabled!=1) return 0;
    return policies.set(id,enabled!=0,value)?1:0;
}
int toi_mod_get_control(uint32_t id,int* enabled,double* value) {
    if(!enabled||!value||!toi::controlSpec(id))return 0;
    auto snapshot=policies.snapshot();*enabled=snapshot.values[id].enabled?1:0;*value=snapshot.values[id].value;return 1;
}
int toi_mod_set_combine_policy(uint32_t mode) {return policies.setCombine(mode)?1:0;}
void toi_mod_reset_settings() {policies.reset();}
uint32_t toi_mod_gameplay_binding_count() {
#ifdef __ANDROID__
return static_cast<uint32_t>(toi::runtimeHookCount());
#else
return 0;
#endif
}
const char* toi_mod_integration_status() {
    return "EXPERIMENTAL v0.3.1: inspect per-control hook/capability/apply diagnostics; gameplay requires device verification; NPC editors excluded";
}
}
