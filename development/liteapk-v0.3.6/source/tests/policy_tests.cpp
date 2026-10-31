#include "modifiers.hpp"
#include "mod_api.h"
#include <cmath>
#include <iostream>
#include <limits>
#include <thread>
#include <vector>

namespace {
int assertions=0;
void check(bool condition,const char* reason){++assertions;if(!condition){std::cerr<<"FAIL: "<<reason<<'\n';std::exit(1);}}
void close(double a,double b,const char* reason){check(std::abs(a-b)<1e-9,reason);}
}
int main(){
    using namespace toi;
    PolicyStore store;
    Scope player{0x100,7,0x900};
    Event event{Kind::OutgoingDamage,Category::Martial,0x100,7,0,10,100,false};
    auto initial=store.snapshot();
    for(uint32_t i=0;i<static_cast<uint32_t>(Control::Count);++i){
        check(!initial.values[i].enabled,"all controls start disabled");
        check(controlSpec(i)!=nullptr,"every policy has a spec");
        check(store.set(i,true,controlSpec(i)->minimum),"inclusive minimum");
        check(store.set(i,true,controlSpec(i)->maximum),"inclusive maximum");
        check(!store.set(i,true,controlSpec(i)->maximum+1),"reject over maximum");
        check(!store.set(i,true,controlSpec(i)->minimum-1),"reject below minimum");
    }
    check(!store.set(99,true,1),"reject nonexistent control");
    check(!store.set(3,true,std::numeric_limits<double>::quiet_NaN()),"reject NaN");
    check(!store.set(3,true,std::numeric_limits<double>::infinity()),"reject infinity");
    check(!store.setCombine(2),"reject undefined combination policy");
    store.reset();
    close(evaluatePolicy(store.snapshot(),player,event).value,10,"OFF preserves damage");
    store.set(3,true,10);store.set(4,true,5);
    close(evaluatePolicy(store.snapshot(),player,event).value,50,"category replaces global");
    store.setCombine(1);
    close(evaluatePolicy(store.snapshot(),player,event).value,500,"explicit product combines once");
    store.set(4,true,100);
    close(evaluatePolicy(store.snapshot(),player,event).value,1000,"combined factor capped at 100");
    event.actor=0x200;
    close(evaluatePolicy(store.snapshot(),player,event).value,10,"enemy damage unchanged");
    event.actor=player.player;event.worldGeneration=8;
    close(evaluatePolicy(store.snapshot(),player,event).value,10,"previous world cannot target player");
    event.worldGeneration=7;event.alreadyApplied=true;
    close(evaluatePolicy(store.snapshot(),player,event).value,10,"already modified event cannot stack");
    event.alreadyApplied=false;
    check(!evaluatePolicy(store.snapshot(),Scope{},event).applied,"unknown player fails closed");
    store.reset();store.set(0,true,1);event.kind=Kind::IncomingDamage;
    close(evaluatePolicy(store.snapshot(),player,event).value,0,"player god protection");
    event.actor=0x200;
    close(evaluatePolicy(store.snapshot(),player,event).value,10,"NPC not protected");
    event.actor=0x100;event.kind=Kind::EnergyCost;store.set(2,true,1);
    close(evaluatePolicy(store.snapshot(),player,event).value,0,"energy lock suppresses cost");
    event.kind=Kind::EnergyResource;
    close(evaluatePolicy(store.snapshot(),player,event).value,100,"energy resource fills max");
    store.reset();store.set(11,true,37);event.kind=Kind::CritChance;
    close(evaluatePolicy(store.snapshot(),player,event).value,37,"rating override is absolute");
    store.reset();store.set(18,true,4);store.set(19,true,3);event.kind=Kind::Exp;event.category=Category::Spot;
    close(evaluatePolicy(store.snapshot(),player,event).value,30,"spot factor independently overrides global");
    store.setCombine(1);
    close(evaluatePolicy(store.snapshot(),player,event).value,120,"spot explicitly combines with global");
    event.actor=0x200;
    close(evaluatePolicy(store.snapshot(),player,event).value,10,"NPC EXP unchanged");
    event.actor=0x100;event.kind=Kind::ArtifactDamage;event.artifact=0x901;store.set(27,true,10);
    close(evaluatePolicy(store.snapshot(),player,event).value,10,"unselected artifact excluded from future policy");
    store.reset();event.kind=Kind::OutgoingDamage;event.category=Category::General;
    close(evaluatePolicy(store.snapshot(),player,event).value,10,"reset restores neutral math");
    double out=-1;
    check(calculateStatEdit(20,Edit::Set,50,0,100,true,out)&&out==50,"SET");
    check(calculateStatEdit(20,Edit::Add,5,0,100,true,out)&&out==25,"ADD");
    check(calculateStatEdit(20,Edit::Subtract,5,0,100,true,out)&&out==15,"SUBTRACT");
    check(calculateStatEdit(20,Edit::Multiply,2.5,0,100,true,out)&&out==50,"MULTIPLY");
    check(!calculateStatEdit(20,Edit::Subtract,21,0,100,true,out),"negative result rejected");
    check(!calculateStatEdit(20,Edit::Multiply,1e300,0,100,true,out),"overflow/range rejected");
    check(!calculateStatEdit(20,Edit(99),1,0,100,true,out),"unknown stat operation rejected");
    check(!calculateStatEdit(20,Edit::Set,NAN,0,100,true,out),"invalid operand rejected");
    check(calculateStatEdit(20,Edit::Multiply,1.23,0,100,true,out)&&out==24,"integer truncation explicit");
    toi_mod_reset_settings();int enabled=-1;double value=-1;
    check(toi_mod_abi_version()==2,"C ABI version");
    check(toi_mod_set_control(3,1,2)==1,"C API set");
    check(toi_mod_get_control(3,&enabled,&value)==1&&enabled==1&&value==2,"C API readback");
    check(toi_mod_set_control(3,2,2)==0,"C API rejects malformed boolean");
    check(toi_mod_get_control(3,nullptr,&value)==0,"C API rejects null output");
    check(toi_mod_gameplay_binding_count()==0,"host cannot claim installed game hooks");
    std::vector<std::thread> threads;
    for(int i=0;i<4;++i)threads.emplace_back([&store,i]{for(int j=0;j<1000;++j){store.set(3,true,1+i);auto s=store.snapshot();if(s.values[3].value<1||s.values[3].value>4)std::abort();}});
    for(auto& t:threads)t.join();
    check(true,"concurrent snapshots are valid");
    std::cout<<"Policy: "<<assertions<<" assertions passed; this is not gameplay/device verification\n";
}
