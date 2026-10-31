#include "managed_access.hpp"
#include <cstring>
#ifdef __ANDROID__
#include <android/log.h>
#endif
namespace toi {
namespace {std::string canonical(std::string s){for(char& c:s)if(c=='/'||c=='+')c='.';return s;}}
void ManagedAccess::reject(std::string why){failed=true;error=context+": "+std::move(why);}
std::string ManagedAccess::typeName(const ManagedType* type){if(!type)return {};auto raw=api->type_get_name(type);if(!raw)return {};std::string name(raw);api->free(raw);return canonical(name);}
ManagedClass* ManagedAccess::klass(const char* name){return api->class_from_name(image,"",name);}
const ManagedMethod* ManagedAccess::method(ManagedClass* cls,const MethodSpec& spec){
    const ManagedMethod* found=nullptr;
    for(int depth=0;cls&&depth<32;cls=api->class_get_parent(cls),++depth){
        void* iter=nullptr;
        while(auto m=api->class_get_methods(cls,&iter)){
            if(std::strcmp(api->method_get_name(m),spec.name)||api->method_get_token(m)!=spec.token||api->method_get_param_count(m)!=spec.parameters.size())continue;
            uint32_t impl{};auto flags=api->method_get_flags(m,&impl);auto rt=api->method_get_return_type(m);auto code=api->type_get_type(rt);
            bool returnMatch=std::strcmp(spec.result,"$ref")==0?(code==0x12||code==0x15||code==0x0e||code==0x1d):typeName(rt)==canonical(spec.result);
            if(bool(flags&0x10)!=spec.isStatic||!returnMatch)continue;
            bool match=true;uint32_t n=0;
            for(auto p:spec.parameters)if(typeName(api->method_get_param(m,n++))!=canonical(p)){match=false;break;}
            if(match){if(found&&found!=m){reject("Ambiguous checked method");return nullptr;}found=m;}
        }
    }
    return found;
}
Object* ManagedAccess::invoke(const ManagedMethod* method,Object* self,void** args){
    failed=false;if(!method){reject("Required game method was not resolved");return nullptr;}
    Object* ex=nullptr;auto result=api->runtime_invoke(method,self,args,&ex);
    if(ex){
        char detail[2048]{},stack[4096]{};
        if(api->format_exception)api->format_exception(ex,detail,sizeof(detail));
        if(api->format_stack_trace)api->format_stack_trace(ex,stack,sizeof(stack));
        auto cls=api->method_get_class(method);auto owner=cls?api->class_get_name(cls):nullptr;auto name=api->method_get_name(method);
        auto ec=api->object_get_class(ex);auto kind=ec?api->class_get_name(ec):nullptr;
        reject("MANAGED_EXCEPTION in "+std::string(owner?owner:"?")+"."+(name?name:"?")+" ["+(kind?kind:"?")+"] "+detail+"\n"+stack);
#ifdef __ANDROID__
        __android_log_print(ANDROID_LOG_ERROR,"TOIModMenu","%s",error.c_str());
#endif
        return nullptr;
    }
    return result;
}
std::string ManagedAccess::text(Object* string){
    if(!string)return {};
    auto n=api->string_length(string);if(n<0||n>8192)return {};auto chars=api->string_chars(string);if(!chars)return {};
    std::string s;s.reserve(size_t(n)*2);
    for(int i=0;i<n;++i){auto c=chars[i];if(c&&c<0x80)s+=char(c);else if(c<0x800){s+=char(0xc0|(c>>6));s+=char(0x80|(c&63));}else{s+=char(0xe0|(c>>12));s+=char(0x80|((c>>6)&63));s+=char(0x80|(c&63));}}
    return s;
}
Object* ManagedAccess::string(const std::string& s){return api->string_new_len(s.data(),uint32_t(s.size()));}
Object* ManagedAccess::objectField(Object* object,const char* name,const char* expected){
    if(!object){reject(std::string("Null owner for field ")+name);return nullptr;}
    auto f=api->class_get_field_from_name(api->object_get_class(object),name);
    if(!f||(api->field_get_flags(f)&0x10)){reject(std::string("Missing instance field ")+name);return nullptr;}
    if(expected&&typeName(api->field_get_type(f))!=canonical(expected)){reject(std::string("Unexpected field type: ")+name);return nullptr;}
    auto type=api->type_get_type(api->field_get_type(f));
    if(type!=0x12&&type!=0x15&&type!=0x0e&&type!=0x1d){reject(std::string("Field is not an object reference: ")+name);return nullptr;}
    Object* value=nullptr;api->field_get_value(object,f,&value);return value;
}
bool ManagedAccess::integerField(Object* object,const char* name,int64_t& out,int type){
    if(!object){reject(std::string("Null owner for numeric field ")+name);return false;}
    auto f=api->class_get_field_from_name(api->object_get_class(object),name);
    if(!f||(api->field_get_flags(f)&0x10)||api->type_get_type(api->field_get_type(f))!=type){reject(std::string("Numeric field type mismatch: ")+name);return false;}
    if(type==8){int v{};api->field_get_value(object,f,&v);out=v;return true;}
    if(type==10){api->field_get_value(object,f,&out);return true;}reject("Unsupported numeric field type");return false;
}
bool ManagedAccess::constant(const char* owner,const char* name,int& out){
    auto c=klass(owner);auto f=c?api->class_get_field_from_name(c,name):nullptr;
    if(!f||!(api->field_get_flags(f)&0x40)||api->type_get_type(api->field_get_type(f))!=8){reject(std::string("Int32 constant unavailable: ")+owner+"."+name);return false;}
    api->field_static_get_value(f,&out);return true;
}
bool ManagedAccess::intResult(const ManagedMethod* method,Object* object,void** args,int& out){
    auto boxed=invoke(method,object,args);if(failed)return false;auto value=boxed?api->object_unbox(boxed):nullptr;
    if(!value){reject("Int32 game result is missing");return false;}std::memcpy(&out,value,sizeof(out));return true;
}
bool ManagedAccess::list(Object* object,Object*& array,int& count){
    if(!object){reject("Game list is not initialized");return false;}
    auto cls=api->object_get_class(object);auto size=api->class_get_field_from_name(cls,"_size");auto items=api->class_get_field_from_name(cls,"_items");
    if(!size||!items||api->type_get_type(api->field_get_type(size))!=8){reject("Game List layout mismatch");return false;}
    api->field_get_value(object,size,&count);api->field_get_value(object,items,&array);
    if(!array||count<0||count>100000||uint32_t(count)>api->array_length(array)){reject("Game list/array bounds rejected");return false;}return true;
}
}
