#include "bridge.hpp"
#include "game_runtime.hpp"
#include "mod_api.h"
#include <jni.h>
#include <android/log.h>
#include <exception>
#include <sstream>

namespace {
std::mutex stateMutex,prepareMutex;
std::shared_ptr<toi::Bridge> current;
std::string initialization="BLOCKED: baseline not prepared; Unity callback adapter not installed";
std::shared_ptr<toi::Bridge> getBridge() {
    std::lock_guard<std::mutex> lock(stateMutex);return current;
}
std::string getString(JNIEnv* env,jstring value) {
    if(!value || env->GetStringUTFLength(value)>4096) return {};
    auto s=env->GetStringUTFChars(value,nullptr);
    if(!s) return {};
    std::string copy(s);env->ReleaseStringUTFChars(value,s);return copy;
}
std::string quoted(const std::string& value) {
    std::ostringstream s;s<<'"';
    constexpr char hex[]="0123456789abcdef";
    for(unsigned char c:value) {
        if(c=='"' || c=='\\') s<<'\\'<<char(c);
        else if(c<32) s<<"\\u00"<<hex[c>>4]<<hex[c&15];
        else s<<char(c);
    }
    s<<'"';return s.str();
}
std::string receipt(const toi::Receipt& r) {
    return "{\"id\":"+std::to_string(r.id)+",\"state\":"+quoted(r.state)+
           ",\"detail\":"+quoted(r.detail)+"}";
}
jstring stringResult(JNIEnv* env,const std::string& value) {
    return env->ExceptionCheck()?nullptr:env->NewStringUTF(value.c_str());
}
jstring enqueue(JNIEnv* env,jlong value,jstring session,toi::Action action) {
    try {
        auto bridge=getBridge();
        if(!bridge) return stringResult(env,"{\"state\":\"BLOCKED\",\"detail\":\"No verified baseline\"}");
        return stringResult(env,receipt(bridge->enqueue(action,value,getString(env,session))));
    } catch(...) { return stringResult(env,"{\"state\":\"ERROR\",\"detail\":\"Native boundary failure\"}"); }
}
}
extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM*,void*) {
    __android_log_print(ANDROID_LOG_INFO,"TOIModMenu","v0.3.1 ARM64 component loaded; hooks await baseline verification");
    return JNI_VERSION_1_6;
}
extern "C" JNIEXPORT jlong JNICALL
Java_org_npc_toibridge_NativeBridge_capabilities(JNIEnv*,jclass) {return static_cast<jlong>(toi::runtimeCapabilities());}
extern "C" JNIEXPORT jint JNICALL
Java_org_npc_toibridge_NativeBridge_bridgeVersion(JNIEnv*,jclass){return 4;}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_takeGameResults(JNIEnv* env,jclass){
    try{
        std::string json="[";
        for(const auto& r:toi::takeGameRequestResults()){
            if(json.size()>1)json+=",";
            json+="{\"id\":"+std::to_string(r.id)+",\"generation\":"+std::to_string(r.generation)+
                  ",\"kind\":"+quoted(r.kind)+",\"key\":"+quoted(r.key)+",\"state\":"+quoted(r.state)+",\"message\":"+quoted(r.message)+"}";
        }
        return stringResult(env,json+"]");
    }catch(...){return stringResult(env,"[]");}
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_applyControl(JNIEnv* env,jclass,jint id,jstring key,jboolean on,jdouble value){
    try{return stringResult(env,toi::controlReplyJson(toi::runtimeApplyControl(id,getString(env,key),on==JNI_TRUE,value)));}
    catch(...){return stringResult(env,"{\"result\":\"NATIVE_REJECTED\",\"detail\":\"JNI control boundary failure\"}");}
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_controlDiagnostics(JNIEnv* env,jclass){
    try{return stringResult(env,toi::runtimeControlDiagnostics());}catch(...){return stringResult(env,"{\"protocol\":4,\"initialized\":false,\"error\":\"Diagnostic boundary failure\"}");}
}
extern "C" JNIEXPORT jboolean JNICALL
Java_org_npc_toibridge_NativeBridge_controlEnabled(JNIEnv*,jclass,jint id) {int enabled=0;double value=0;return toi_mod_get_control(static_cast<uint32_t>(id),&enabled,&value)&&enabled?JNI_TRUE:JNI_FALSE;}
extern "C" JNIEXPORT jboolean JNICALL
Java_org_npc_toibridge_NativeBridge_setControl(JNIEnv*,jclass,jint id,jboolean enabled,jdouble value) {
    try{auto spec=id>=0?toi::controlSpec(uint32_t(id)):nullptr;if(!spec)return JNI_FALSE;return toi::runtimeApplyControl(id,spec->key,enabled==JNI_TRUE,value).code=="APPLIED"?JNI_TRUE:JNI_FALSE;}catch(...){return JNI_FALSE;}
}
extern "C" JNIEXPORT void JNICALL
Java_org_npc_toibridge_NativeBridge_resetControls(JNIEnv*,jclass) {try{toi_mod_reset_settings();}catch(...) {}}
extern "C" JNIEXPORT void JNICALL
Java_org_npc_toibridge_NativeBridge_closeMenu(JNIEnv*,jclass) {try{toi_mod_reset_settings();toi::cancelGameRequests();if(auto b=getBridge())b->disarm("Activity closed");}catch(...) {}}
extern "C" JNIEXPORT jboolean JNICALL
Java_org_npc_toibridge_NativeBridge_setCombine(JNIEnv*,jclass,jint mode) {try{return toi_mod_set_combine_policy(static_cast<uint32_t>(mode))?JNI_TRUE:JNI_FALSE;}catch(...){return JNI_FALSE;}}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_request(JNIEnv* env,jclass,jstring kind,jstring key,jint op,jdouble value,jboolean backup) {
    try {
        auto k=getString(env,kind);bool readOnly=k=="read"||k=="catalog"||((k=="currency"||k=="capacity")&&op==-1);
        if(!readOnly&&backup!=JNI_TRUE)return stringResult(env,"Backup acknowledgment required for persistent edits");
        std::string error;
        auto id=toi::queueGameRequest(k,getString(env,key),op,value,error);
        return stringResult(env,id?"QUEUED:"+std::to_string(id):error);
    }catch(...){return stringResult(env,"ERROR: request boundary");}
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_result(JNIEnv* env,jclass) {try{return stringResult(env,toi::gameRequestResult());}catch(...){return stringResult(env,"ERROR");}}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_prepare(JNIEnv* env,jclass,jstring library,jstring metadata) {
    try {
        std::lock_guard<std::mutex> prepareLock(prepareMutex);
        if(toi::runtimeHookCount()>0)return stringResult(env,"BASELINE_MATCHED; runtime already prepared");
        if(auto previous=getBridge()) previous->disarm("Re-preparing baseline");
        std::string error;
        auto backend=toi::makeIl2CppBackend(getString(env,library),getString(env,metadata),error);
        {std::lock_guard<std::mutex> lock(stateMutex);current=backend?std::make_shared<toi::Bridge>(backend):nullptr;initialization=backend?"BASELINE_MATCHED":error;}
        if(backend && !toi::startGameRuntime(backend,error))return stringResult(env,error);
        return stringResult(env,backend?"BASELINE_MATCHED; Unity adapter installed — runtime untested":error);
    } catch(...) { return stringResult(env,"BLOCKED: native preparation failure"); }
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_armExperiment(JNIEnv* env,jclass,jstring session,
                                               jboolean backup,jboolean experimental) {
    try {
        auto bridge=getBridge();std::string error;
        if(!bridge) return stringResult(env,"BLOCKED: no verified baseline");
        if(!bridge->arm(getString(env,session),backup==JNI_TRUE,experimental==JNI_TRUE,error))
            return stringResult(env,error);
        return stringResult(env,bridge->status());
    } catch(...) { return stringResult(env,"BLOCKED: native arm failure"); }
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_enqueueExpProbe(JNIEnv* env,jclass,jlong value,jstring session) {
    return enqueue(env,value,session,toi::Action::AddExpProbe);
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_enqueueHpProbe(JNIEnv* env,jclass,jlong value,jstring session) {
    return enqueue(env,value,session,toi::Action::AddHpProbe);
}
extern "C" JNIEXPORT void JNICALL
Java_org_npc_toibridge_NativeBridge_disarm(JNIEnv*,jclass) {
    try { if(auto bridge=getBridge()) bridge->disarm(); } catch(...) {}
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_status(JNIEnv* env,jclass) {
    try {
        if(auto bridge=getBridge()) return stringResult(env,toi::runtimeStatus());
        std::lock_guard<std::mutex> lock(stateMutex);return stringResult(env,initialization);
    } catch(...) { return stringResult(env,"BLOCKED: native status failure"); }
}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_takeReceipts(JNIEnv* env,jclass) {
    try {
        std::string json="[";
        if(auto bridge=getBridge()) for(const auto& r:bridge->takeReceipts()) {
            if(json.size()>1) json+=",";
            json+=receipt(r);
        }
        return stringResult(env,json+"]");
    } catch(...) { return stringResult(env,"[]"); }
}
// Called by the verified baseline UnitySynchronizationContext.ExecuteTasks adapter.
extern "C" __attribute__((visibility("default"))) void toi_bridge_pump() noexcept {
    try { if(auto bridge=getBridge()) bridge->pump(); }
    catch(...) { try { if(auto bridge=getBridge()) bridge->disarm("Native callback failure"); } catch(...) {} }
}
extern "C" __attribute__((visibility("default"))) void toi_bridge_disarm() noexcept {
    try { if(auto bridge=getBridge()) bridge->disarm("World/lifecycle transition"); } catch(...) {}
}
