#include "editor_math.hpp"
#include "request_mailbox.hpp"
#include "managed_access.hpp"
#include "game_editors.hpp"
#include "catalog_utils.hpp"
#include <algorithm>
#include <atomic>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <set>
#include <stdexcept>
#include <thread>
#include <vector>
namespace {
int checks=0;
void check(bool condition,const char* why){++checks;if(!condition)throw std::runtime_error(why);}
void amounts(){
    toi::AmountPlan p;std::string e;
    check(toi::planAmount(10,0,25,2000000000,p,e)&&p.target==25&&p.delta==15,"SET computes delta");
    check(toi::planAmount(10,1,25,2000000000,p,e)&&p.target==35,"ADD");
    check(toi::planAmount(10,2,10,2000000000,p,e)&&p.target==0,"SUBTRACT to zero");
    check(!toi::planAmount(10,2,11,2000000000,p,e),"No overspend");
    check(!toi::planAmount(2000000000,1,1,2000000000,p,e),"Int32 overflow/limit");
    check(!toi::planAmount(-1,0,5,2000000000,p,e),"Negative current balance rejected");
    check(!toi::planAmount(1,1,-1,2000000000,p,e),"Negative operand rejected");
    check(!toi::planAmount(1,0,1.25,2000000000,p,e),"Fractional values rejected");
    check(!toi::planAmount(1,0,std::numeric_limits<double>::quiet_NaN(),2000000000,p,e),"NaN rejected");
    check(!toi::planAmount(1,0,std::numeric_limits<double>::infinity(),2000000000,p,e),"Infinity rejected");
    check(!toi::planAmount(1,3,1,2000000000,p,e),"Invalid operation rejected");
    check(!toi::planAmount(1,-1,1,2000000000,p,e),"READ cannot mutate");
    check(toi::planAmount(500000000000LL,1,500000000000.0,1000000000000LL,p,e)&&p.target==1000000000000LL,"Int64 treasury amount retained");
    check(!toi::planAmount(1000000000000LL,1,1,1000000000000LL,p,e),"Int64 bound");
    check(!toi::planAmount(1,0,1,std::numeric_limits<int64_t>::max(),p,e),"Double-to-int64 invalid bound refused");
    for(int64_t current:{0LL,1LL,100LL,1999999999LL,2000000000LL})for(int64_t operand:{0LL,1LL,50LL,1000LL,2000000000LL}){
        bool ok=toi::planAmount(current,1,double(operand),2000000000,p,e);
        check(ok==(current+operand<=2000000000),"ADD boundary matrix");
        if(ok)check(p.target==current+operand&&p.before==current,"Exact ADD result");
        ok=toi::planAmount(current,2,double(operand),2000000000,p,e);
        check(ok==(operand<=current),"SUB boundary matrix");if(ok)check(p.target==current-operand,"Exact SUB result");
    }
}
void capacity(){
    toi::AmountPlan p;std::string e;int bonus{};
    for(int add:{50,100,200}){
        check(toi::planCapacity(52,30,1,0,1,add,p,bonus,e)&&p.target==52+add&&bonus==add,"Requested slot addition is exact");
        check(toi::planCapacity(104,30,2,0,1,add,p,bonus,e)&&p.target==104+add&&bonus==add/2,"Existing bag plugin does not double requested addition");
    }
    check(!toi::planCapacity(52,40,1,0,0,39,p,bonus,e),"SET protects occupied items");
    check(!toi::planCapacity(52,40,1,0,2,13,p,bonus,e),"SUB protects occupied items");
    check(toi::planCapacity(252,40,1,200,0,52,p,bonus,e)&&bonus==0,"Explicit capacity restore when items fit");
    check(!toi::planCapacity(52,1,1,0,0,0,p,bonus,e),"Minimum one slot");
    check(!toi::planCapacity(104,40,2,0,1,1,p,bonus,e),"Plugin parity checked");
    check(!toi::planCapacity(52,0,3,0,1,100,p,bonus,e),"Unknown capacity formula rejected");
    check(!toi::planCapacity(52,-1,1,0,1,100,p,bonus,e),"Missing occupancy rejected");
    check(!toi::planCapacity(52,0,1,0,0,2001,p,bonus,e),"Capacity cap");
}
void mailbox(){
    toi::RequestMailbox box;auto now=toi::RequestMailbox::Clock::now();
    auto currency=box.submit("currency","money",1,100,7,now);auto catalog=box.submit("catalog","@-1||0",0,0,7,now);
    toi::GameRequest q;check(box.pop(q)&&q.id==currency,"First request preserved");box.finish(q,"APPLIED","10 -> 110");
    check(box.pop(q)&&q.id==catalog,"Independent catalog request");auto expiry=q.expiry;box.defer(q);
    check(box.pop(q)&&q.id==catalog&&q.expiry==expiry,"Deferral preserves ID and expiry");box.finish(q,"CATALOG","rows");
    auto results=box.take();check(results.size()==2&&results[0].id==currency&&results[1].id==catalog,"Catalog cannot overwrite currency result");
    check(results[0].message=="10 -> 110"&&results[0].generation==7,"Typed receipt context");check(box.take().empty(),"Receipts drained exactly once");
    for(int i=0;i<32;++i)check(box.submit("read","hp",0,0,8)!=0,"Queue accepts bounded requests");
    check(box.submit("item","1",0,1,8)==0,"Queue full rejects without execution");box.cancel("world changed");results=box.take();
    check(results.size()==32,"Every cancellation has receipt");for(const auto& r:results)check(r.state=="CANCELLED"&&r.message=="world changed","Cancellation context");
    check(!box.pop(q),"Cancelled work cannot execute");
    std::vector<std::thread> threads;std::atomic<int> submitted{};
    for(int t=0;t<8;++t)threads.emplace_back([&]{for(int i=0;i<3;++i)if(box.submit("currency","money",1,1,9))++submitted;});
    for(auto& thread:threads)thread.join();
    std::set<uint64_t> ids;
    while(box.pop(q)){ids.insert(q.id);box.finish(q,"READ","done");}
    check(submitted==24&&ids.size()==24,"Concurrent producers have unique IDs");check(box.take().size()==24,"Concurrent requests retain individual results");
}
struct FakeType {const char* name;int code;};
struct FakeClass;
struct FakeMethod {const char* name;uint32_t token;FakeType* result;std::vector<FakeType*> params;bool isStatic;FakeClass* owner;};
struct FakeClass {const char* name;FakeClass* parent;std::vector<FakeMethod*> methods;};
FakeClass exceptionClass{"NullReferenceException",nullptr,{}};bool throwManaged=false;int boxed=42;
void managed(){
    FakeType i32{"System.Int32",8},str{"System.String",14},ref{"DataBuildSchool+SchoolData",18};
    FakeClass parent{"Parent",nullptr,{}},child{"Child",&parent,{}};
    FakeMethod method{"Action",0x06001234,&i32,{&i32},false,&parent};parent.methods={&method};
    toi::ManagedApi a{};
    a.class_get_parent=[](void* c)->void*{return static_cast<FakeClass*>(c)->parent;};
    a.class_get_methods=[](void* c,void** it)->const void*{auto& m=static_cast<FakeClass*>(c)->methods;auto n=reinterpret_cast<uintptr_t>(*it);if(n>=m.size())return nullptr;*it=reinterpret_cast<void*>(n+1);return m[n];};
    a.method_get_name=[](const void* m){return static_cast<const FakeMethod*>(m)->name;};
    a.method_get_token=[](const void* m){return static_cast<const FakeMethod*>(m)->token;};
    a.method_get_param_count=[](const void* m){return uint32_t(static_cast<const FakeMethod*>(m)->params.size());};
    a.method_get_param=[](const void* m,uint32_t n)->const void*{return static_cast<const FakeMethod*>(m)->params[n];};
    a.method_get_flags=[](const void* m,uint32_t*){return static_cast<const FakeMethod*>(m)->isStatic?uint32_t(16):uint32_t(0);};
    a.method_get_return_type=[](const void* m)->const void*{return static_cast<const FakeMethod*>(m)->result;};
    a.type_get_type=[](const void* t){return static_cast<const FakeType*>(t)->code;};
    a.type_get_name=[](const void* t){return strdup(static_cast<const FakeType*>(t)->name);};a.free=std::free;
    a.runtime_invoke=[](const void*,void*,void**,void** ex)->void*{if(throwManaged){*ex=&exceptionClass;return nullptr;}return &boxed;};
    a.object_get_class=[](void*)->void*{return &exceptionClass;};a.class_get_name=[](void* c){return static_cast<FakeClass*>(c)->name;};
    a.method_get_class=[](const void* m)->void*{return static_cast<const FakeMethod*>(m)->owner;};a.object_unbox=[](void* b){return b;};
    a.format_exception=[](void*,char* dst,int n){std::strncpy(dst,"missing UI reference",size_t(n)-1);};
    a.format_stack_trace=[](void*,char* dst,int n){std::strncpy(dst,"at SchoolData.AddMoney / UI refresh",size_t(n)-1);};
    toi::ManagedAccess m{&a,nullptr,false,"","Currency sect_funds"};
    toi::MethodSpec spec{"Action",0x06001234,"System.Int32",{"System.Int32"}};
    check(m.method(&child,spec)==&method,"Checked method resolves inherited implementation");
    check(!m.method(&child,{"Action",0x06001235,"System.Int32",{"System.Int32"}}),"Wrong token rejected");
    check(!m.method(&child,{"Action",0x06001234,"System.String",{"System.Int32"}}),"Wrong result rejected");
    check(!m.method(&child,{"Action",0x06001234,"System.Int32",{"System.String"}}),"Wrong parameter rejected");
    check(!m.method(&child,{"Action",0x06001234,"System.Int32",{"System.Int32"},true}),"Wrong calling convention rejected");
    check(!m.method(&child,{"Action",0x06001234,"$ref",{"System.Int32"}}),"Boxed result cannot masquerade as reference");
    method.result=&ref;check(m.method(&child,{"Action",0x06001234,"DataBuildSchool.SchoolData",{"System.Int32"}})==&method,"Nested type canonicalization");
    check(m.method(&child,{"Action",0x06001234,"$ref",{"System.Int32"}})==&method,"Reference return token checked");method.result=&i32;
    int value{};check(m.intResult(&method,&child,nullptr,value)&&value==42,"Unboxed Int32 readback");
    throwManaged=true;check(!m.invoke(&method,&child)&&m.failed,"Managed exception is not hidden");
    check(m.error.find("Currency sect_funds")!=std::string::npos&&m.error.find("Parent.Action")!=std::string::npos&&m.error.find("missing UI reference")!=std::string::npos&&m.error.find("at SchoolData")!=std::string::npos,"Exception includes operation, method, detail and stack");
    throwManaged=false;check(m.invoke(&method,&child)&&!m.failed,"Later read can run after captured mutation exception");
    check(!m.invoke(nullptr)&&m.failed,"Unresolved function never invoked");
    method.params={&str};check(!m.method(&child,spec),"Overload mismatch fails closed");
}
void catalog(){
    toi::CatalogQuery q;
    check(toi::parseCatalogQuery("@-1||0",q)&&q.type==-1&&q.term.empty()&&q.offset==0,"Browse without typing");
    check(toi::parseCatalogQuery("@2|Cres|40",q)&&q.type==2&&q.offset==40,"Category and pagination");
    for(auto bad:{"", "@-2||0", "@1||-1", "@1x||0", "@1||999999999999999", "@1|a|b|0", "@1|a|0junk"})check(!toi::parseCatalogQuery(bad,q),"Malformed query rejected");
    check(toi::matchRank("Crescent Manual","456","cReS")==0,"Case insensitive prefix");
    check(toi::matchRank("Great Crescent","456","cres")==1,"Substring ranked after prefix");
    check(toi::matchRank("中文丹方","456","丹方")==1,"Chinese alias search");
    check(toi::matchRank("Manual","456","45")==0,"ID prefix");
    check(toi::safeCatalogName("A\tB\nC")=="A B C","Protocol delimiters escaped");
    toi::GameEditors editor;auto reply=editor.process({});check(reply.state=="BLOCKED","Uninitialized editor cannot mutate");
    int npc=0;check(editor.modifyCapacity(&npc,52)==52,"No bonus applied before player binding");
}
}
int main(){try{amounts();capacity();mailbox();managed();catalog();std::cout<<"PASS: "<<checks<<" checks; host logic only, no Android/device test\n";return 0;}catch(const std::exception& e){std::cerr<<"FAIL after "<<checks<<" checks: "<<e.what()<<'\n';return 1;}}
