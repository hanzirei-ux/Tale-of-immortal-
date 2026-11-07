#include "managed_access.hpp"
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
using namespace toi;
struct C {const char* name;};
struct T {const char* name;int type;};
struct M {const char* name;unsigned token;T* ret;T* args[2];unsigned count;unsigned flags;};
static C owner{"DataProps"},nestedData{"PropsData"},nestedArtifact{"PropsArtifact"},world{"WorldUnitData"};
static T propType{"DataProps/PropsData",0x12},receiptType{"WorldUnitData+RewardItemData",0x15},
         boolType{"System.Boolean",2},gameRewardType{"GameItemRewardData",0x12};
static M add{"AddProps",0x060084f6,&receiptType,{&propType,nullptr},1,0};
static M reward{"RewardItem",0x06015a90,&receiptType,{&gameRewardType,&boolType},2,0};
static ManagedClass* findClass(const void*,const char* ns,const char* name){
  if(std::strcmp(ns,""))return nullptr;
  if(!std::strcmp(name,"DataProps"))return &owner;
  if(!std::strcmp(name,"WorldUnitData"))return &world;
  return nullptr;
}
static ManagedClass* getNested(ManagedClass* c,void** iter){
  if(c!=&owner)return nullptr;
  auto n=reinterpret_cast<uintptr_t>(*iter);
  *iter=reinterpret_cast<void*>(n+1);
  if(n==0)return &nestedData;
  if(n==1)return &nestedArtifact;
  return nullptr;
}
static const char* className(ManagedClass* c){return static_cast<C*>(c)->name;}
static ManagedClass* parent(ManagedClass*){return nullptr;}
static const ManagedMethod* methods(ManagedClass* c,void** iter){
  auto n=reinterpret_cast<uintptr_t>(*iter);
  *iter=reinterpret_cast<void*>(n+1);
  if(n)return nullptr;
  if(c==&owner)return &add;
  if(c==&world)return &reward;
  return nullptr;
}
static const char* methodName(const ManagedMethod* p){return static_cast<const M*>(p)->name;}
static uint32_t token(const ManagedMethod* p){return static_cast<const M*>(p)->token;}
static uint32_t count(const ManagedMethod* p){return static_cast<const M*>(p)->count;}
static const ManagedType* param(const ManagedMethod* p,uint32_t i){return static_cast<const M*>(p)->args[i];}
static const ManagedType* result(const ManagedMethod* p){return static_cast<const M*>(p)->ret;}
static uint32_t flags(const ManagedMethod* p,uint32_t*){return static_cast<const M*>(p)->flags;}
static int typeCode(const ManagedType* p){return static_cast<const T*>(p)->type;}
static char* typeName(const ManagedType* p){return strdup(static_cast<const T*>(p)->name);}
int main(){
  ManagedApi a{};
  a.class_from_name=findClass;a.class_get_nested_types=getNested;a.class_get_name=className;
  a.class_get_methods=methods;a.class_get_parent=parent;a.method_get_name=methodName;
  a.method_get_token=token;a.method_get_param_count=count;a.method_get_param=param;
  a.method_get_return_type=result;a.method_get_flags=flags;a.type_get_type=typeCode;
  a.type_get_name=typeName;a.free=std::free;
  ManagedAccess ma{};ma.api=&a;
  assert(ma.klass("DataProps.PropsData")==&nestedData);
  assert(ma.klass("DataProps.PropsArtifact")==&nestedArtifact);
  assert(ma.klass("PropsData")==nullptr);
  assert(ma.klass("DataProps.Unknown")==nullptr);
  assert(ma.klass("WorldUnitData")==&world);
  MethodSpec correctAdd{"AddProps",0x060084f6,"$ref",{"DataProps.PropsData"}};
  MethodSpec wrongAdd{"AddProps",0x060084f6,"$ref",{"PropsData"}};
  MethodSpec correctReward{"RewardItem",0x06015a90,"WorldUnitData.RewardItemData",{"GameItemRewardData","System.Boolean"}};
  MethodSpec wrongReward{"RewardItem",0x06015a90,"RewardItemData",{"GameItemRewardData","System.Boolean"}};
  MethodSpec wrongToken{"RewardItem",0x06015a91,"WorldUnitData.RewardItemData",{"GameItemRewardData","System.Boolean"}};
  assert(ma.method(&owner,correctAdd));
  assert(!ma.method(&owner,wrongAdd));
  assert(ma.method(&world,correctReward));
  assert(!ma.method(&world,wrongReward));
  assert(!ma.method(&world,wrongToken));
  std::cout<<"PASS nested lookup, canonical plus/slash type names, strict signature/token checks\n";
}
