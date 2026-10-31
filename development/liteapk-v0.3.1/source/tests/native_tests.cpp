#include "bridge.hpp"
#include "sha256.hpp"
#include <functional>
#include <iostream>
#include <set>
#include <stdexcept>

namespace {
int checks=0,cases=0;
void check(bool ok,const char* msg) { ++checks;if(!ok) throw std::runtime_error(msg); }
struct FakeBackend : toi::Backend {
    std::thread::id main=std::this_thread::get_id();
    int mainChecks{},signatureChecks{},calls{};
    bool signature=true,exception=false,throwNative=false;
    std::string last;
    std::function<void()> beforeInvoke,beforeVerify;
    bool verifyMainThread(std::string& error) override {
        ++mainChecks;
        if(throwNative) throw std::runtime_error("Simulated native failure");
        if(beforeVerify) beforeVerify();
        if(std::this_thread::get_id()!=main) { error="Wrong thread";return false; }
        return true;
    }
    bool verifyDispatcher(std::string& error) override {
        ++signatureChecks;if(!signature) error="Wrong signature";return signature;
    }
    toi::Invocation invoke(const std::string& s) override {
        ++calls;last=s;if(beforeInvoke) beforeInvoke();
        return {exception,exception?"Simulated managed exception":"SIMULATION ONLY"};
    }
};
struct Fixture {
    std::shared_ptr<FakeBackend> backend=std::make_shared<FakeBackend>();
    toi::Bridge bridge{backend};
    std::string error;
    void arm(const std::string& s="backup-test") { check(bridge.arm(s,true,true,error),"arm"); }
    toi::Receipt exp(int64_t n=10,const std::string& s="backup-test",toi::Bridge::Clock::time_point t=toi::Bridge::Clock::now()) {
        return bridge.enqueue(toi::Action::AddExpProbe,n,s,t);
    }
};
void run(const char* name,const std::function<void()>& f) { f();++cases;std::cout<<"PASS "<<name<<'\n'; }
}
int main() {
 try {
    run("sha256-empty",[]{toi::Sha256 h;check(h.finish()=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","empty hash");});
    run("sha256-abc",[]{toi::Sha256 h;h.update("a",1);h.update("bc",2);check(h.finish()=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","abc hash");});
    run("sha256-million-a",[]{toi::Sha256 h;std::string s(1000,'a');for(int i=0;i<1000;++i)h.update(s.data(),s.size());check(h.finish()=="cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0","million a hash");});
    run("bounded-probe-grammar",[]{std::string c,e;check(toi::makeProbeCommand(toi::Action::AddExpProbe,100,c,e)&&c=="jingyan_100","exp grammar");check(toi::makeProbeCommand(toi::Action::AddHpProbe,10,c,e)&&c=="shuxing_hp_10","hp grammar");for(auto n:{-1LL,0LL,101LL,9223372036854775807LL})check(!toi::makeProbeCommand(toi::Action::AddExpProbe,n,c,e),"reject bad EXP");check(!toi::makeProbeCommand(toi::Action::AddHpProbe,11,c,e),"HP cap");});
    run("no-invented-item-layout",[]{std::string c,e;check(!toi::makeProbeCommand(toi::Action::AddItem,1,c,e)&&c.empty(),"item remains blocked");});
    run("missing-backend-blocks",[]{toi::Bridge b(nullptr);std::string e;check(!b.arm("backup",true,true,e),"backend required");});
    run("acknowledgments-required",[]{Fixture f;check(!f.bridge.arm("backup",false,true,f.error),"backup required");check(!f.bridge.arm("backup",true,false,f.error),"experiment required");});
    run("invalid-session-rejected",[]{Fixture f;for(auto s:{"","a_b","abc\n","bad;id"})check(!f.bridge.arm(s,true,true,f.error),"session grammar");check(!f.bridge.arm(std::string(65,'a'),true,true,f.error),"session cap");});
    run("startup-does-not-invoke",[]{Fixture f;f.bridge.pump();check(f.backend->mainChecks==0&&f.backend->calls==0,"no startup calls");check(f.exp().state=="REJECTED","not armed");});
    run("wrong-session-rejected",[]{Fixture f;f.arm();check(f.exp(10,"other-save").state=="REJECTED","world mismatch");});
    run("enqueue-does-not-invoke",[]{Fixture f;f.arm();check(f.exp().state=="QUEUED","queued");check(f.backend->mainChecks==0&&f.backend->calls==0,"JNI producer must not invoke");});
    run("dispatch-once-unverified",[]{Fixture f;f.arm();auto r=f.exp();f.bridge.pump();f.bridge.pump();auto results=f.bridge.takeReceipts();check(f.backend->calls==1&&f.backend->last=="jingyan_10","exactly once");check(results.size()==1&&results[0].id==r.id&&results[0].state=="INVOKED_UNVERIFIED","not gameplay verified");});
    run("one-command-per-frame",[]{Fixture f;f.arm();f.exp(1);f.exp(2);f.bridge.pump();check(f.backend->calls==1,"frame budget");f.bridge.pump();check(f.backend->calls==2,"next frame");});
    run("expired-request-not-executed",[]{Fixture f;f.arm();auto t=toi::Bridge::Clock::now();f.exp(10,"backup-test",t);f.bridge.pump(t+std::chrono::seconds(10));auto r=f.bridge.takeReceipts();check(f.backend->calls==0&&r[0].state=="EXPIRED","TTL");});
    run("disable-clears-queue",[]{Fixture f;f.arm();f.exp();f.bridge.disarm();f.bridge.pump();check(f.backend->calls==0&&f.bridge.takeReceipts()[0].state=="CANCELLED","cancel");});
    run("new-session-cancels-old",[]{Fixture f;f.arm();f.exp();f.arm("new-save");f.bridge.pump();check(f.backend->calls==0,"old queued command cancelled");check(f.exp().state=="REJECTED","old session invalidated");});
    run("worker-thread-rejected",[]{Fixture f;f.arm();f.exp();std::thread worker([&]{f.bridge.pump();});worker.join();check(f.backend->calls==0&&f.backend->signatureChecks==0,"wrong thread stops before dispatcher lookup");check(f.bridge.takeReceipts()[0].state=="BLOCKED","thread status");});
    run("signature-mismatch-rejected",[]{Fixture f;f.arm();f.backend->signature=false;f.exp();f.bridge.pump();check(f.backend->calls==0,"bad signature not invoked");check(f.exp().state=="REJECTED","re-arm required");});
    run("managed-exception-disarms",[]{Fixture f;f.arm();f.backend->exception=true;f.exp();f.exp();f.bridge.pump();f.bridge.pump();auto r=f.bridge.takeReceipts();check(f.backend->calls==1&&r.size()==2&&r[0].state=="MANAGED_EXCEPTION"&&r[1].state=="CANCELLED","exception cancels pending");});
    run("native-exception-contained",[]{Fixture f;f.arm();f.backend->throwNative=true;f.exp();f.bridge.pump();check(f.backend->calls==0&&f.bridge.takeReceipts()[0].state=="NATIVE_EXCEPTION","C++ exception boundary");});
    run("recursion-does-not-double-dispatch",[]{Fixture f;f.arm();f.exp();f.exp();f.backend->beforeInvoke=[&]{f.bridge.pump();};f.bridge.pump();check(f.backend->calls==1,"recursive pump ignored");});
    run("disable-during-validation-cancels",[]{Fixture f;f.arm();f.exp();f.backend->beforeVerify=[&]{f.bridge.disarm();};f.bridge.pump();check(f.backend->calls==0&&f.bridge.takeReceipts()[0].state=="CANCELLED","epoch gate");});
    run("bounded-queue",[]{Fixture f;f.arm();for(int i=0;i<32;++i)check(f.exp().state=="QUEUED","queue room");check(f.exp().state=="REJECTED","queue cap");});
    run("concurrent-producers",[]{Fixture f;f.arm();std::mutex m;std::set<uint64_t> ids;std::vector<std::thread> workers;for(int i=0;i<4;++i)workers.emplace_back([&]{for(int k=0;k<8;++k){auto r=f.exp();std::lock_guard<std::mutex> lock(m);ids.insert(r.id);}});for(auto& t:workers)t.join();check(ids.size()==32&&f.backend->calls==0,"unique IDs, no worker dispatch");for(int i=0;i<32;++i)f.bridge.pump();check(f.backend->calls==32,"queued once");});
    run("bounded-receipt-history",[]{Fixture f;f.arm();for(int batch=0;batch<3;++batch){for(int i=0;i<32;++i)f.exp();for(int i=0;i<32;++i)f.bridge.pump();}check(f.bridge.takeReceipts().size()==64,"receipt memory bound");});
    run("real-backend-rejects-missing-files",[]{std::string e;check(!toi::makeIl2CppBackend("/missing/libil2cpp.so","/missing/metadata.dat",e)&&!e.empty(),"fail closed baseline");});
    std::cout<<"RESULT: "<<cases<<" host test cases, "<<checks<<" assertions. NO GAME/ANDROID TESTS.\n";
    return 0;
 } catch(const std::exception& e) {std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}
