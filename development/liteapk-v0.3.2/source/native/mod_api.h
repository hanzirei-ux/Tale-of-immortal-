#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define TOI_API __attribute__((visibility("default")))
TOI_API uint32_t toi_mod_abi_version(void);
TOI_API uint32_t toi_mod_control_count(void);
TOI_API const char* toi_mod_control_key(uint32_t id);
TOI_API int toi_mod_set_control(uint32_t id,int enabled,double value);
TOI_API int toi_mod_get_control(uint32_t id,int* enabled,double* value);
TOI_API int toi_mod_set_combine_policy(uint32_t mode);
TOI_API void toi_mod_reset_settings(void);
// Number of successfully installed native hooks; this is not device verification.
TOI_API uint32_t toi_mod_gameplay_binding_count(void);
TOI_API const char* toi_mod_integration_status(void);
#ifdef __cplusplus
}
#endif
