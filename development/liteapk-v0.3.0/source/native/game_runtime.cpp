#include "game_runtime.hpp"
#include "baseline_profile.hpp"
#include "catalog_utils.hpp"
#include "game_editors.hpp"
#include "managed_access.hpp"
#include "request_mailbox.hpp"
#include <functional>
#include "dobby.h"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstring>
#include <cctype>
#include <limits>
#include <dlfcn.h>
#include <sstream>
#include <sys/syscall.h>
#include <unistd.h>
#include <vector>

extern "C" void toi_bridge_pump() noexcept;
extern "C" void toi_bridge_disarm() noexcept;
namespace toi {
namespace {
using Obj=void;using Method=void;using Class=void;using Field=void;using Type=void;
template<class T>T read(Obj* object,size_t offset) {T v{};if(object)std::memcpy(&v,static_cast<char*>(object)+offset,sizeof(v));return v;}
template<class T>void write(Obj* object,size_t offset,T value) {if(object)std::memcpy(static_cast<char*>(object)+offset,&value,sizeof(value));}
using Api=ManagedApi;
struct Binding {Obj* value;Control control;bool divide;};
pid_t threadId(){thread_local const pid_t id=pid_t(syscall(SYS_gettid));return id;}
struct Runtime {
    Api a{};ManagedAccess managed{};GameEditors editors{};RequestMailbox mailbox;uintptr_t base{};void* handle{};const void* image{};
    std::shared_ptr<Backend> backend;
    std::atomic<pid_t> mainTid{};bool initialized{},failed{},invokeFailed{},statusPublished{};int contextAttempts{};std::atomic<int> hooks{};
    std::atomic<uint64_t> generation{};
    std::atomic<uint64_t> capabilities{};
    Policy p=defaults();Obj *world{},*player{},*worldData{},*dyn{},*unitInfo{},*property{},*combat{};
    uint64_t activeDynMask{};
    Class *playerClass{},*dynClass{};
    const Method *worldGetter{},*confGetter{},*baseGetter{},*baseSetter{},*minGetter{},*maxGetter{},*rewardItem{},*itemConfGetter{},*itemListGetter{};
    std::vector<Binding> bindings;
    std::mutex mutex;std::string status="Waiting for Unity callback",result="No request";
    bool isMain()const{auto tid=mainTid.load(std::memory_order_relaxed);return tid && threadId()==tid;}
    bool active()const{return isMain()&&initialized&&!failed;}
    void setStatus(std::string s){std::lock_guard<std::mutex> l(mutex);status=std::move(s);}
    Class* klass(const char* name){return a.class_from_name(image,"",name);}
    const Method* method(Class* c,const char* name,uint32_t count,int firstType=-1) {
        if(!c)return nullptr;
        void* it=nullptr;const Method* found=nullptr;
        while(auto m=a.class_get_methods(c,&it))if(std::strcmp(a.method_get_name(m),name)==0 && a.method_get_param_count(m)==count &&
                (firstType<0 || a.type_get_type(a.method_get_param(m,0))==firstType)) {
            if(found)return nullptr;
            found=m;
        }
        return found;
    }
    Obj* invoke(const Method* m,Obj* self=nullptr,void** args=nullptr) {
        auto value=managed.invoke(m,self,args);invokeFailed=managed.failed;
        if(invokeFailed){std::lock_guard<std::mutex> l(mutex);result=managed.error;}
        return value;
    }
    std::string text(Obj* string) {
        if(!string)return {};
        auto n=a.string_length(string);if(n<0||n>4096)return {};
        auto chars=a.string_chars(string);std::string s;
        for(int32_t i=0;i<n;++i){auto c=chars[i];if(c<0x80)s+=char(c);else if(c<0x800){s+=char(0xc0|(c>>6));s+=char(0x80|(c&63));}else{s+=char(0xe0|(c>>12));s+=char(0x80|((c>>6)&63));s+=char(0x80|(c&63));}}
        return s;
    }
    bool playerCtrl(Obj* ctrl) {return ctrl && player && a.object_get_class(ctrl)==playerClass && read<Obj*>(ctrl,0x398)==player;}
    Setting setting(Control c)const{return p.values[static_cast<size_t>(c)];}
    double factor(Control c)const{auto s=setting(c);return s.enabled?s.value:1;}
    bool enabled(Control c)const{return setting(c).enabled;}
    int scaled(int v,double f)const{return int(std::clamp(static_cast<double>(v)*f,-2000000000.0,2000000000.0));}
    double combined(Control c)const{auto s=setting(c);return !s.enabled?factor(Control::AllDamage):p.combine==Combine::CategoryOverride?s.value:std::min(100.0,factor(Control::AllDamage)*s.value);}
    void frame();bool init();void process();void refreshBindings();
};
Runtime runtime;
PolicyStore policyStore;
thread_local int dynDepth=0,expDepth=0,hpDepth=0;
thread_local bool inSpot=false,inManual=false;
struct Depth {int& n;explicit Depth(int& v):n(v){++n;}~Depth(){--n;}};
struct BoolScope {bool& value;bool previous;BoolScope(bool& v,bool next):value(v),previous(v){v=next;}~BoolScope(){value=previous;}};
void (*origFrame)(const Method*);
void (*origPlayerInit)(Obj*,Obj*,int,const Method*);
void (*origPlayerDestroy)(Obj*,bool,const Method*);
bool (*origPlayerDie)(Obj*,bool,Obj*,const Method*);
void (*origHP)(Obj*,Obj*,const Method*);
void (*origMP)(Obj*,int,bool,const Method*);
int (*origInt)(Obj*,const Method*);float (*origFloat)(Obj*,const Method*);
int (*origExp)(Obj*,int,const Method*),(*origFixExp)(Obj*,int,const Method*);
void (*origSpot)(Obj*,const Method*),(*origManual)(Obj*,const Method*);
void (*origMartialExp)(Obj*,Obj*,int,const Method*);
float (*origCooldown)(Obj*,const Method*);
Obj* (*origShot)(Obj*,const Method*);
template<class T>T function(const profile::Site& s){T f{};auto ptr=reinterpret_cast<void*>(runtime.base+s.rva);std::memcpy(&f,&ptr,sizeof(f));return f;}
using Getter=Obj*(*)(Obj*,const Method*);
Obj* getUnit(Obj* d){return function<Getter>(profile::DataUnit)(d,nullptr);}
Obj* getAttacker(Obj* h){return function<Getter>(profile::HitAttacker)(h,nullptr);}
Obj* skillOwner(Obj* d) {auto s=function<Getter>(profile::DataSkill)(d,nullptr);return s?function<Getter>(profile::SkillOwner)(s,nullptr):nullptr;}
double modifyDyn(Obj* object,double value) {
    if(!runtime.isMain()||!runtime.initialized||runtime.failed)return value;
    value=runtime.editors.modifyCapacity(object,value);
    if(!runtime.activeDynMask)return value;
    for(const auto& b:runtime.bindings)if(b.value==object) {
        auto s=runtime.setting(b.control);if(!s.enabled)return value;
        if(b.control==Control::CritChance||b.control==Control::CritResistance)return s.value; // native ratings, not percentage
        return b.divide?value/s.value:value*s.value;
    }
    return value;
}
int hookInt(Obj* o,const Method* m){Depth d(dynDepth);auto v=origInt(o,m);return dynDepth==1?int(std::clamp(modifyDyn(o,v),-2000000000.0,2000000000.0)):v;}
float hookFloat(Obj* o,const Method* m){Depth d(dynDepth);auto v=origFloat(o,m);return dynDepth==1?float(modifyDyn(o,v)):v;}
void hookInit(Obj* self,Obj* data,int type,const Method* m){origPlayerInit(self,data,type,m);if(runtime.isMain()&&runtime.playerCtrl(self))runtime.combat=self;}
void hookDestroy(Obj* self,bool effect,const Method* m){if(runtime.isMain()&&runtime.combat==self){runtime.combat=nullptr;runtime.bindings.clear();}origPlayerDestroy(self,effect,m);}
bool hookDie(Obj* self,bool effect,Obj* hit,const Method* m){if(runtime.active()&&runtime.playerCtrl(self)&&runtime.enabled(Control::GodMode))return false;return origPlayerDie(self,effect,hit,m);}
void hookHP(Obj* self,Obj* hit,const Method* m) {
    Depth nesting(hpDepth);
    if(!runtime.isMain()||!runtime.initialized||runtime.failed||!hit){origHP(self,hit,m);return;}
    int old=read<int>(hit,0x70),value=old;
    auto target=getUnit(self);bool own=runtime.playerCtrl(target);
    if(own)runtime.combat=target;
    if(old<0 && own && (runtime.enabled(Control::GodMode)||runtime.enabled(Control::HpLock)))value=0;
    else if(old<0 && hpDepth==1 && runtime.playerCtrl(getAttacker(hit))) {
        Control c=Control::AllDamage;auto skill=read<Obj*>(hit,0x90);auto attacker=getAttacker(hit);
        if(skill && skill==read<Obj*>(attacker,0x88) && runtime.enabled(Control::UltimateDamage))c=Control::UltimateDamage;
        else if(skill && runtime.enabled(Control::SkillDamage))c=Control::SkillDamage;
        else if(read<int>(hit,0x6c)>0 && runtime.enabled(Control::SpiritualDamage))c=Control::SpiritualDamage;
        else if(read<int>(hit,0x68)>0 && runtime.enabled(Control::MartialDamage))c=Control::MartialDamage;
        double f=c==Control::AllDamage?runtime.factor(c):runtime.combined(c);
        if(read<uint8_t>(hit,0x74))f*=runtime.factor(Control::CritDamage);
        value=runtime.scaled(old,std::min(100.0,f));
    }
    if(value==old){origHP(self,hit,m);return;}
    struct Restore {Obj* hit;int before;~Restore(){write(hit,0x70,before);}} restore{hit,old};
    write(hit,0x70,value);origHP(self,hit,m);
}
void hookMP(Obj* self,int value,bool show,const Method* m) {
    if(runtime.active() && value<0 && runtime.playerCtrl(getUnit(self)))
        value=runtime.enabled(Control::EnergyLock)?0:runtime.scaled(value,runtime.factor(Control::EnergyCost));
    origMP(self,value,show,m);
}
double combinedExp(Control category) {auto& r=runtime;if(r.enabled(category))return r.p.combine==Combine::CategoryOverride?r.factor(category):std::min(100.0,r.factor(Control::AllExp)*r.factor(category));return r.factor(Control::AllExp);}
double expFactor() {return inSpot?combinedExp(Control::SpotExp):runtime.factor(Control::AllExp);}
int hookExp(Obj* self,int v,const Method* m){Depth d(expDepth);if(expDepth==1&&runtime.active()&&self==runtime.property&&v>0)v=runtime.scaled(v,expFactor());return origExp(self,v,m);}
int hookFixExp(Obj* self,int v,const Method* m){Depth d(expDepth);if(expDepth==1&&runtime.active()&&self==runtime.property&&v>0)v=runtime.scaled(v,expFactor());return origFixExp(self,v,m);}
void hookSpot(Obj* self,const Method* m){BoolScope scope(inSpot,runtime.isMain()&&read<Obj*>(self,0x10)==runtime.player);origSpot(self,m);}
void hookManual(Obj* self,const Method* m){BoolScope scope(inManual,runtime.isMain()&&read<Obj*>(self,0x10)==runtime.player);origManual(self,m);}
void hookMartialExp(Obj* self,Obj* id,int exp,const Method* m){if(runtime.active()&&self==runtime.unitInfo&&exp>0)exp=runtime.scaled(exp,combinedExp(inManual?Control::ManualExp:Control::SkillExp));origMartialExp(self,id,exp,m);}
float hookCooldown(Obj* self,const Method* m){auto v=origCooldown(self,m);if(runtime.active()&&runtime.enabled(Control::Cooldown)&&runtime.playerCtrl(skillOwner(self)))return float(v*runtime.factor(Control::Cooldown));return v;}
Obj* hookShot(Obj* self,const Method* m){auto d=origShot(self,m);if(runtime.active()&&runtime.enabled(Control::AttackSpeed)&&d&&runtime.playerCtrl(skillOwner(self))&&runtime.bindings.size()<128) {
    if(std::none_of(runtime.bindings.begin(),runtime.bindings.end(),[d](const Binding& b){return b.value==d;}))runtime.bindings.push_back({d,Control::AttackSpeed,true});
}return d;}
void hookFrame(const Method* m){origFrame(m);try{runtime.frame();}catch(...){runtime.failed=true;runtime.capabilities=0;runtime.setStatus("FAILED: native frame boundary; restart with mods OFF");}}
template<class T>bool hook(const profile::Site& site,T replacement,T& original) {
    auto address=reinterpret_cast<void*>(runtime.base+site.rva);
    if(std::memcmp(address,site.prologue,16)!=0)return false;
    dobby_dummy_func_t fake{};std::memcpy(&fake,&replacement,sizeof(fake));
    if(DobbyHook(address,fake,reinterpret_cast<dobby_dummy_func_t*>(&original))!=0||!original)return false;
    // This Dobby revision can log a code-patch failure without propagating it.
    // Do not expose a capability when the verified entry bytes remain intact.
    if(std::memcmp(address,site.prologue,16)==0)return false;
    ++runtime.hooks;return true;
}
bool Runtime::init() {
#define LOAD(n) do{auto v=dlsym(handle,"il2cpp_" #n);if(!v){setStatus("Missing API: il2cpp_" #n);return false;}std::memcpy(&a.n,&v,sizeof(v));}while(false)
    LOAD(domain_get);LOAD(domain_get_assemblies);LOAD(assembly_get_image);LOAD(image_get_name);LOAD(class_from_name);
    LOAD(object_get_class);LOAD(class_get_name);LOAD(class_get_methods);LOAD(method_get_name);LOAD(method_get_param_count);
    LOAD(method_get_param);LOAD(type_get_type);LOAD(class_get_field_from_name);LOAD(field_get_offset);LOAD(field_get_value);
    LOAD(runtime_invoke);LOAD(string_length);LOAD(string_chars);LOAD(string_new_len);LOAD(array_length);
    LOAD(class_get_parent);LOAD(field_get_type);LOAD(field_get_flags);LOAD(field_static_get_value);
    LOAD(method_get_token);LOAD(method_get_flags);LOAD(method_get_return_type);LOAD(method_get_class);
    LOAD(type_get_name);LOAD(free);LOAD(object_unbox);LOAD(format_exception);LOAD(format_stack_trace);
#undef LOAD
    size_t n{};auto as=a.domain_get_assemblies(a.domain_get(),&n);if(!as||n>4096)return false;
    for(size_t i=0;i<n;++i){auto im=a.assembly_get_image(as[i]);if(std::strcmp(a.image_get_name(im),"Assembly-CSharp.dll")==0)image=im;}
    if(!image)return false;
    managed.api=&a;managed.image=image;managed.context="Runtime initialization";editors.initialize(managed);
    playerClass=klass("UnitCtrlPlayer");dynClass=klass("DynInt");
    struct Check{const char* type;const char* field;size_t offset;};
    for(auto c:{Check{"WorldUnitBase","data",0x68},Check{"WorldUnitData","dynUnitData",0x30},Check{"WorldUnitData","unitData",0x28},Check{"WorldMgr","playerUnit",0x10},
                Check{"UnitCtrlBase","data",0x70},Check{"UnitCtrlBase","ultimate",0x88},Check{"UnitCtrlPlayer","unit",0x398},Check{"UnitDataBase","hp",0x60},Check{"UnitDataBase","defense",0xb0},Check{"UnitDataBase","mp",0x64},
                Check{"UnitDataBase","maxHP",0x70},Check{"UnitDataBase","maxMP",0x78},Check{"UnitDataBase","crit",0xd8},Check{"UnitDataBase","guard",0xe8},
                Check{"UnitDataBase","moveSpeed",0xd0},Check{"UnitDataBase","phycicalFree",0xf8},Check{"UnitDataBase","magicFree",0x100},
                Check{"WorldUnitDynData","propGridNum",0x270}}) {
        auto k=klass(c.type);auto f=k?a.class_get_field_from_name(k,c.field):nullptr;
        if(!f||a.field_get_offset(f)!=c.offset){setStatus("Field layout mismatch: "+std::string(c.type)+"."+c.field);return false;}
    }
    worldGetter=method(klass("g"),"get_world",0);confGetter=method(klass("g"),"get_conf",0);
    baseGetter=method(dynClass,"get_baseValue",0);baseSetter=method(dynClass,"set_baseValue",1);
    minGetter=method(dynClass,"get_minValue",0);maxGetter=method(dynClass,"get_maxValue",0);
    rewardItem=method(klass("WorldUnitData"),"RewardPropItem",3,8);
    itemConfGetter=method(klass("ConfMgr"),"get_itemProps",0);itemListGetter=method(klass("ConfItemPropsBase"),"get_allConfList",0);
    if(!worldGetter||!baseGetter||!baseSetter||!minGetter||!maxGetter||!playerClass){setStatus("FAILED: required runtime method missing or ambiguous");return false;}
    bool hi=hook(profile::DynInt,hookInt,origInt),hf=hook(profile::DynFloat,hookFloat,origFloat);
    bool hp=hook(profile::AddHP,hookHP,origHP),mp=hook(profile::AddMP,hookMP,origMP);
    bool die=hook(profile::PlayerDie,hookDie,origPlayerDie);
    hook(profile::PlayerInit,hookInit,origPlayerInit);hook(profile::PlayerDestroy,hookDestroy,origPlayerDestroy);
    bool exp=hook(profile::AddExp,hookExp,origExp),fix=hook(profile::AddFixExp,hookFixExp,origFixExp);
    bool spot=hook(profile::SpotExp,hookSpot,origSpot),manual=hook(profile::ManualTrain,hookManual,origManual);
    bool martial=hook(profile::ManualExp,hookMartialExp,origMartialExp),cd=hook(profile::Cooldown,hookCooldown,origCooldown);
    bool shot=hook(profile::Shot,hookShot,origShot);
    uint64_t mask=0;auto cap=[&](Control c,bool yes){if(yes)mask|=uint64_t(1)<<static_cast<uint32_t>(c);};
    cap(Control::GodMode,hp&&die);cap(Control::HpLock,hp&&hi);cap(Control::EnergyLock,mp&&hi);
    for(auto c:{Control::AllDamage,Control::MartialDamage,Control::SpiritualDamage,Control::SkillDamage,Control::UltimateDamage,Control::CritDamage})cap(c,hp);
    for(auto c:{Control::Defense,Control::MartialResistance,Control::SpiritualResistance,Control::CritChance,Control::CritResistance,Control::MovementSpeed})cap(c,hi&&hf);
    cap(Control::AttackSpeed,hi&&hf&&shot);cap(Control::Cooldown,cd);cap(Control::EnergyCost,mp);
    cap(Control::AllExp,exp&&fix);cap(Control::SpotExp,exp&&fix&&spot);cap(Control::ManualExp,martial&&manual);cap(Control::SkillExp,martial);
    capabilities=mask;bindings.reserve(128);return true;
}
void Runtime::refreshBindings() {
    bindings.clear();if(!playerCtrl(combat)){combat=nullptr;return;}
    auto data=read<Obj*>(combat,0x70);if(!data)return;
    for(auto b:{Binding{read<Obj*>(data,0xb0),Control::Defense,false},Binding{read<Obj*>(data,0xf8),Control::MartialResistance,false},
                 Binding{read<Obj*>(data,0x100),Control::SpiritualResistance,false},Binding{read<Obj*>(data,0xd8),Control::CritChance,false},
                 Binding{read<Obj*>(data,0xe8),Control::CritResistance,false},Binding{read<Obj*>(data,0xd0),Control::MovementSpeed,false}})
        if(b.value)bindings.push_back(b);
    if(enabled(Control::HpLock)){auto max=read<Obj*>(data,0x70);if(max)write(data,0x60,std::max(1,origInt(max,nullptr)));}
    if(enabled(Control::EnergyLock)){auto max=read<Obj*>(data,0x78);if(max)write(data,0x64,std::max(0,origInt(max,nullptr)));}
}
void Runtime::frame() {
    if(failed)return;
    if(!initialized) {
        std::string e;if(!backend->verifyMainThread(e)){if(++contextAttempts>=120){failed=true;setStatus("FAILED: Unity context not verified after 120 callbacks: "+e);}else if(contextAttempts==1)setStatus("Waiting for verified Unity context: "+e);return;}
        mainTid=threadId();
        if(!init()){failed=true;capabilities=0;return;}initialized=true;
    }
    if(!isMain())return;
    p=policyStore.snapshot();
    auto available=capabilities.load();for(size_t i=0;i<p.values.size();++i)if(!(available&(uint64_t(1)<<i)))p.values[i].enabled=false;
    activeDynMask=0;for(auto c:{Control::Defense,Control::MartialResistance,Control::SpiritualResistance,Control::CritChance,Control::CritResistance,Control::MovementSpeed,Control::AttackSpeed})if(enabled(c))activeDynMask|=uint64_t(1)<<static_cast<uint32_t>(c);
    auto previousWorld=world;auto previousInfo=unitInfo;auto previousDyn=dyn;auto previousData=worldData;world=invoke(worldGetter);auto previous=player;
    player=world&&!read<uint8_t>(world,0x108)?read<Obj*>(world,0x10):nullptr;
    worldData=read<Obj*>(player,0x68);dyn=read<Obj*>(worldData,0x30);unitInfo=read<Obj*>(worldData,0x28);property=read<Obj*>(unitInfo,0x10);
    if(previous!=player||previousWorld!=world||previousInfo!=unitInfo||previousDyn!=dyn||previousData!=worldData){combat=nullptr;bindings.clear();++generation;toi_bridge_disarm();}
    if(player)refreshBindings();else {combat=nullptr;bindings.clear();}
    editors.bind({player,worldData,dyn,unitInfo,read<Obj*>(unitInfo,0x90),generation.load()});
    process();toi_bridge_pump();
    if(!statusPublished||previous!=player){statusPublished=true;setStatus("COMPILED — RUNTIME UNTESTED | hooks="+std::to_string(hooks.load())+" | player="+(player?"loaded":"not loaded"));}
}
// Persistent edits use native DynInt methods via runtime_invoke, never raw save writes.
void Runtime::process() {
    GameRequest q;if(!mailbox.pop(q))return;
    bool replied=false;
    auto finish=[this,&q,&replied](std::string s){replied=true;mailbox.finish(q,"RESULT",s);std::lock_guard<std::mutex> l(mutex);result=std::move(s);};
    struct ReplyGuard {std::function<void()> fn;~ReplyGuard(){fn();}} guard{[&]{if(!replied)finish(managed.failed?managed.error:"Operation did not produce a result; no success confirmed");}};
    managed.context=q.kind+" ["+q.key+"]";managed.failed=false;managed.error.clear();
    if(q.expiry<=Bridge::Clock::now()){finish("EXPIRED; no change");return;}
    if(q.generation!=generation.load()){finish("CANCELLED: world/save changed");return;}
    if(!player||!worldData||!dyn){finish("Player save/world must be loaded");return;}
    if(q.kind=="currency"||q.kind=="capacity"||q.kind=="catalog"||q.kind=="item") {
        auto reply=editors.process(q);replied=true;
        if(reply.deferred){mailbox.defer(std::move(q));return;}
        mailbox.finish(q,reply.state,reply.message);
        {std::lock_guard<std::mutex> l(mutex);result=reply.state+": "+reply.message;}
        return;
    }
    if(q.kind=="gm") {
        std::string why;if(!backend->verifyMainThread(why)||!backend->verifyDispatcher(why)){finish(why);return;}
        auto done=backend->invoke(q.key);finish(done.exception?done.detail:"INVOKED_UNVERIFIED: "+done.detail);return;
    }
    if(q.kind=="stat"||q.kind=="read") {
        static const char* allowed="|hp|hpMax|mp|mpMax|attack|defense|crit|critValue|guard|guardValue|phycicalFree|magicFree|moveSpeed|luck|life|health|healthMax|energy|energyMax|mood|moodMax|talent|abilityPoint|basisFire|basisFroze|basisThunder|basisWind|basisEarth|basisWood|basisBlade|basisSpear|basisSword|basisFist|basisPalm|basisFinger|refineElixir|refineWeapon|geomancy|symbol|herbal|mine|propGridNum|";
        if(q.key.empty()||!std::strstr(allowed,("|"+q.key+"|").c_str())){finish("Attribute is not in the player-only allowlist");return;}
        auto f=a.class_get_field_from_name(a.object_get_class(dyn),q.key.c_str());Obj* value=nullptr;if(f)a.field_get_value(dyn,f,&value);
        if(!value||a.object_get_class(value)!=dynClass){finish("Attribute unavailable or not DynInt");return;}
        auto boxed=invoke(baseGetter,value);if(!boxed){finish("Cannot read base value");return;}
        auto unbox=reinterpret_cast<void*(*)(Obj*)>(dlsym(handle,"il2cpp_object_unbox"));if(!unbox){finish("Unbox API unavailable");return;}
        int before{};std::memcpy(&before,unbox(boxed),sizeof(before));
        if(q.kind=="read"){finish(q.key+" base="+std::to_string(before));return;}
        // The matching propGridNum base setter is a no-op. Use the Capacity Editor.
        if(q.key=="propGridNum"&&q.kind=="stat") {
            finish("Use the persistent Capacity Editor; propGridNum base setter is a no-op");return;
        }
        double after{},limit=10000000;
        double minimum=(q.key=="hpMax"||q.key=="life")?1:0;
        auto lower=invoke(minGetter,value);if(!lower){if(!invokeFailed)finish("Cannot read attribute minimum");return;}int engineMin{};std::memcpy(&engineMin,unbox(lower),sizeof(engineMin));
        auto upper=invoke(maxGetter,value);if(!upper){if(!invokeFailed)finish("Cannot read attribute maximum");return;}int engineMax{};std::memcpy(&engineMax,unbox(upper),sizeof(engineMax));
        minimum=std::max(minimum,double(engineMin));limit=std::min(limit,double(engineMax));
        if(!calculateStatEdit(before,static_cast<Edit>(q.op),q.value,minimum,limit,true,after)){finish("Edit rejected by numeric limits");return;}

        int next=int(after);void* args[]{&next};invoke(baseSetter,value,args);if(invokeFailed)return;
        auto check=invoke(baseGetter,value);if(invokeFailed)return;
        if(!check){finish("Setter invoked; readback unavailable, verify in game");return;}
        int observed{};std::memcpy(&observed,unbox(check),sizeof(observed));
        finish(q.key+": "+std::to_string(before)+" -> "+std::to_string(observed)+"; save/load untested");return;
    }
    finish("Unsupported request");
}
}
PolicyStore& runtimePolicyStore(){return policyStore;}
bool startGameRuntime(std::shared_ptr<Backend> backend,std::string& error) {
    if(runtime.hooks.load()>0){error="Runtime already prepared";return true;}
    if(runtime.handle){dlclose(runtime.handle);runtime.handle=nullptr;}
    runtime.backend=std::move(backend);runtime.handle=dlopen("libil2cpp.so",RTLD_NOW|RTLD_NOLOAD);
    Dl_info info{};auto symbol=runtime.handle?dlsym(runtime.handle,"il2cpp_domain_get"):nullptr;
    if(!symbol||!dladdr(symbol,&info)){error="Loaded IL2CPP base unavailable";runtime.setStatus(error);return false;}
    runtime.base=reinterpret_cast<uintptr_t>(info.dli_fbase);
    if(!hook(profile::UnityFrame,hookFrame,origFrame)){error="Unity callback prologue mismatch or hook installation failed";runtime.setStatus(error);return false;}
    return true;
}
std::string runtimeStatus(){std::lock_guard<std::mutex> l(runtime.mutex);return runtime.status;}
uint64_t runtimeCapabilities(){return runtime.capabilities.load();}
int runtimeHookCount(){return runtime.hooks.load();}
uint64_t queueGameRequest(const std::string& kind,const std::string& key,int op,double value,std::string& error) {
    if(kind!="stat"&&kind!="read"&&kind!="catalog"&&kind!="item"&&kind!="gm"&&kind!="capacity"&&kind!="currency"){error="Request kind rejected";return false;}
    if(kind=="gm") {
        bool allowed=key=="huifu"||key=="xiulifabao_0"||key=="xiulianmiji"||key=="xueximiji"||key=="citiaomanji"||key=="tupocailiao_1"||key=="haotianyanjiesuojineng";
        if(key.rfind("jingyan_",0)==0||key.rfind("shuangyupei_",0)==0) {
            auto tail=key.substr(key.find('_')+1);allowed=!tail.empty()&&tail.size()<=7&&std::all_of(tail.begin(),tail.end(),[](char c){return c>='0'&&c<='9';});
        }
        if(!allowed){error="Command not in player-only allowlist";return false;}
    }
    if(key.size()>128||!std::isfinite(value)){error="Input rejected";return false;}
    if((kind=="capacity"||kind=="currency")&&(op< -1||op>2||value<0||value!=std::trunc(value))){error="Use READ, SET, ADD, or SUBTRACT with a non-negative whole amount";return 0;}
    if(kind=="capacity"&&key!="slots"){error="Capacity key rejected";return 0;}
    if(kind=="catalog") {
        // Limit untrusted filtering/pagination input; native parser validates again.
        if(key.empty()||key[0]!='@'||std::count(key.begin(),key.end(),'|')!=2) {
            error="Malformed catalog query";return false;
        }
    }
    auto id=runtime.mailbox.submit(kind,key,op,value,runtime.generation.load());if(!id)error="Queue full";return id;
}
std::string gameRequestResult(){std::lock_guard<std::mutex> l(runtime.mutex);return runtime.result;}
std::vector<GameReply> takeGameRequestResults(){return runtime.mailbox.take();}
void cancelGameRequests(){runtime.mailbox.cancel("Activity closed; action was not executed");std::lock_guard<std::mutex> l(runtime.mutex);runtime.result="CANCELLED: Activity closed";}

} // namespace toi
