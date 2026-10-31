#pragma once
#include <cstddef>
#include <cstdint>
#include <initializer_list>
#include <string>
namespace toi {
using Object=void;using ManagedClass=void;using ManagedMethod=void;using ManagedField=void;using ManagedType=void;
struct ManagedApi {
    void* (*domain_get)();const void** (*domain_get_assemblies)(void*,size_t*);
    const void* (*assembly_get_image)(const void*);const char* (*image_get_name)(const void*);
    ManagedClass* (*class_from_name)(const void*,const char*,const char*);
    ManagedClass* (*object_get_class)(Object*);const char* (*class_get_name)(ManagedClass*);
    const ManagedMethod* (*class_get_methods)(ManagedClass*,void**);const char* (*method_get_name)(const ManagedMethod*);
    uint32_t (*method_get_param_count)(const ManagedMethod*);const ManagedType* (*method_get_param)(const ManagedMethod*,uint32_t);
    int (*type_get_type)(const ManagedType*);ManagedField* (*class_get_field_from_name)(ManagedClass*,const char*);
    size_t (*field_get_offset)(ManagedField*);void (*field_get_value)(Object*,ManagedField*,void*);
    Object* (*runtime_invoke)(const ManagedMethod*,void*,void**,Object**);
    int32_t (*string_length)(Object*);const uint16_t* (*string_chars)(Object*);
    Object* (*string_new_len)(const char*,uint32_t);uint32_t (*array_length)(Object*);
    ManagedClass* (*class_get_parent)(ManagedClass*);
    const ManagedType* (*field_get_type)(ManagedField*);int (*field_get_flags)(ManagedField*);
    void (*field_static_get_value)(ManagedField*,void*);
    uint32_t (*method_get_token)(const ManagedMethod*);uint32_t (*method_get_flags)(const ManagedMethod*,uint32_t*);
    const ManagedType* (*method_get_return_type)(const ManagedMethod*);ManagedClass* (*method_get_class)(const ManagedMethod*);
    char* (*type_get_name)(const ManagedType*);void (*free)(void*);void* (*object_unbox)(Object*);
    void (*format_exception)(Object*,char*,int);void (*format_stack_trace)(Object*,char*,int);
    const char* (*class_get_namespace)(ManagedClass*);
};
struct MethodSpec {const char* name;uint32_t token;const char* result;std::initializer_list<const char*> parameters;bool isStatic=false;};
struct ManagedAccess {
    ManagedApi* api{};const void* image{};bool failed{};std::string error,context;
    std::string exceptionType{},exceptionNamespace{},exceptionOwner{},exceptionMethod{};
    void reject(std::string);
    std::string typeName(const ManagedType*);
    ManagedClass* klass(const char* name);
    const ManagedMethod* method(ManagedClass*,const MethodSpec&);
    const ManagedMethod* objectMethod(Object* object,const MethodSpec& spec){return object?method(api->object_get_class(object),spec):nullptr;}
    Object* invoke(const ManagedMethod*,Object* self=nullptr,void** args=nullptr,bool expectedMissingLocalization=false);
    bool consumeMissingLocalization();
    std::string text(Object*);Object* string(const std::string&);
    Object* objectField(Object*,const char*,const char* expectedType=nullptr);
    bool integerField(Object*,const char*,int64_t& out,int type=8);
    bool constant(const char*,const char*,int&);
    bool intResult(const ManagedMethod*,Object*,void**,int&);
    bool list(Object*,Object*&,int&);
};
}
