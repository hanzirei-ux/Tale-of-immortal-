#include "bridge.hpp"
#include "sha256.hpp"
#include <cstring>
#include <dlfcn.h>
#include <limits>
#include <sys/stat.h>
#include <elf.h>
#include <fstream>
#include <array>

namespace toi {
namespace {
// Opaque types only: no MethodInfo layout or game-object offsets are assumed.
struct Domain; struct Assembly; struct Image; struct Class; struct Method;
struct Type; struct Object; struct String; struct Exception; struct Thread; struct Field;
struct Api {
    Domain* (*domain_get)(){};
    const Assembly** (*domain_get_assemblies)(const Domain*,size_t*){};
    const Image* (*assembly_get_image)(const Assembly*){};
    const char* (*image_get_name)(const Image*){};
    Class* (*class_from_name)(const Image*,const char*,const char*){};
    const Method* (*class_get_methods)(Class*,void**){};
    const char* (*class_get_name)(Class*){};
    const char* (*class_get_namespace)(Class*){};
    Field* (*class_get_field_from_name)(Class*,const char*){};
    const Type* (*field_get_type)(Field*){};
    int (*field_get_flags)(Field*){};
    void (*field_get_value)(Object*,Field*,void*){};
    const char* (*method_get_name)(const Method*){};
    uint32_t (*method_get_param_count)(const Method*){};
    const Type* (*method_get_param)(const Method*,uint32_t){};
    const Type* (*method_get_return_type)(const Method*){};
    uint32_t (*method_get_flags)(const Method*,uint32_t*){};
    uint32_t (*method_get_token)(const Method*){};
    bool (*method_is_generic)(const Method*){};
    bool (*method_is_inflated)(const Method*){};
    char* (*type_get_name)(const Type*){};
    int (*type_get_type)(const Type*){};
    Object* (*runtime_invoke)(const Method*,void*,void**,Exception**){};
    String* (*string_new_len)(const char*,uint32_t){};
    Class* (*object_get_class)(Object*){};
    Object* (*object_new)(Class*){};
    void* (*object_unbox)(Object*){};
    Thread* (*thread_current)(){};
    uint32_t (*gchandle_new)(Object*,bool){};
    Object* (*gchandle_get_target)(uint32_t){};
    void (*gchandle_free)(uint32_t){};
    void (*free)(void*){};
    void (*format_exception)(Exception*,char*,int){};
    void (*format_stack_trace)(Exception*,char*,int){};
};
bool sameFile(const std::string& a,const std::string& b) {
    struct stat x{},y{};
    return stat(a.c_str(),&x)==0 && stat(b.c_str(),&y)==0 &&
           S_ISREG(x.st_mode) && x.st_dev==y.st_dev && x.st_ino==y.st_ino;
}
bool mappedExecutableMatches(const std::string& path,const void* loadedBase) {
    std::ifstream f(path,std::ios::binary);Elf64_Ehdr h{};f.read(reinterpret_cast<char*>(&h),sizeof(h));
    if(!f||std::memcmp(h.e_ident,ELFMAG,SELFMAG)!=0||h.e_machine!=EM_AARCH64||h.e_phnum>32||h.e_phentsize!=sizeof(Elf64_Phdr))return false;
    std::vector<Elf64_Phdr> segments(h.e_phnum);f.seekg(static_cast<std::streamoff>(h.e_phoff));f.read(reinterpret_cast<char*>(segments.data()),std::streamsize(segments.size()*sizeof(Elf64_Phdr)));if(!f)return false;
    std::array<char,65536> buffer{};size_t checked=0;
    for(const auto& s:segments)if(s.p_type==PT_LOAD&&(s.p_flags&PF_X)) {
        if(!(s.p_flags&PF_R))return false;
        f.seekg(static_cast<std::streamoff>(s.p_offset));
        for(uint64_t offset=0;offset<s.p_filesz;) {
            auto n=std::min<uint64_t>(buffer.size(),s.p_filesz-offset);f.read(buffer.data(),static_cast<std::streamsize>(n));if(!f)return false;
            auto address=static_cast<const char*>(loadedBase)+s.p_vaddr+offset;
            if(std::memcmp(address,buffer.data(),size_t(n))!=0)return false;
            offset+=n;
        }++checked;
    }
    return checked>0;
}
bool baseline(const std::string& library,const std::string& metadata,std::string& error) {
    std::string hash;
    if (!hashFile(library,hash,error)) return false;
    if (hash!="c477a5637b89f78ca449ff65ad4c9137296ba680923b602db50831ecb5901099") {
        error="libil2cpp hash differs from the specified LiteAPK baseline";return false;
    }
    if (!hashFile(metadata,hash,error)) return false;
    if (hash!="9be3762476a87e8be23e3fa589b44f084027a5c7f1ff78b9be5f013fb5d131b3") {
        error="Metadata hash differs from the specified baseline";return false;
    }
    return true;
}
class Il2CppBackend final : public Backend {
public:
    ~Il2CppBackend() override { if(handle_) dlclose(handle_); }
    bool initialize(const std::string& library,const std::string& metadata,std::string& error) {
        if (!baseline(library,metadata,error)) return false;
#ifdef RTLD_NOLOAD
        handle_=dlopen("libil2cpp.so",RTLD_NOW|RTLD_NOLOAD);
#else
        error="RTLD_NOLOAD unavailable; refusing to load the game library";return false;
#endif
        if(!handle_) { error="libil2cpp is not already loaded; retry after Unity startup";return false; }
#define LOAD_API(name) do { \
    auto symbol=dlsym(handle_,"il2cpp_" #name); \
    if(!symbol) { error="Missing export: il2cpp_" #name;return false; } \
    static_assert(sizeof(a_.name)==sizeof(symbol),"Unsupported function-pointer ABI"); \
    std::memcpy(&a_.name,&symbol,sizeof(symbol)); \
} while(false)
        LOAD_API(domain_get);LOAD_API(domain_get_assemblies);LOAD_API(assembly_get_image);
        LOAD_API(image_get_name);LOAD_API(class_from_name);LOAD_API(class_get_methods);
        LOAD_API(class_get_name);LOAD_API(class_get_namespace);LOAD_API(class_get_field_from_name);
        LOAD_API(field_get_type);LOAD_API(field_get_flags);LOAD_API(field_get_value);
        LOAD_API(method_get_name);LOAD_API(method_get_param_count);LOAD_API(method_get_param);
        LOAD_API(method_get_return_type);LOAD_API(method_get_flags);LOAD_API(method_get_token);
        LOAD_API(method_is_generic);LOAD_API(method_is_inflated);LOAD_API(type_get_name);
        LOAD_API(type_get_type);LOAD_API(runtime_invoke);LOAD_API(string_new_len);
        LOAD_API(object_get_class);LOAD_API(object_new);LOAD_API(object_unbox);LOAD_API(thread_current);
        LOAD_API(gchandle_new);LOAD_API(gchandle_get_target);LOAD_API(gchandle_free);LOAD_API(free);
        LOAD_API(format_exception);LOAD_API(format_stack_trace);
#undef LOAD_API
        Dl_info info{};
        if(!dladdr(dlsym(handle_,"il2cpp_domain_get"),&info) || !info.dli_fname) {error="Loaded IL2CPP identity unavailable";return false;}
        if(!sameFile(library,info.dli_fname)) {
            std::string loaded(info.dli_fname);
            if(loaded.find("!/lib/arm64-v8a/libil2cpp.so")==std::string::npos || !mappedExecutableMatches(library,info.dli_fbase)) {
                error="Loaded IL2CPP executable does not match the hashed baseline";return false;
            }
        }
        return true;
    }
    bool verifyMainThread(std::string& error) override {
        // Attaching an Android/UI worker does NOT make it Unity's scripting thread.
        if(!a_.thread_current()) { error="Caller is not an attached IL2CPP thread";return false; }
        if(!resolveFramework(error)) return false;
        auto context=call(currentContext_,nullptr,nullptr,error);
        if(!context) { if(error.empty()) error="No current SynchronizationContext";return false; }
        auto klass=a_.object_get_class(context);
        auto className=klass?a_.class_get_name(klass):nullptr;
        auto namespaceName=klass?a_.class_get_namespace(klass):nullptr;
        if(!className || !namespaceName || std::strcmp(className,"UnitySynchronizationContext")!=0 ||
           std::strcmp(namespaceName,"UnityEngine")!=0) {
            error="Current context is not UnitySynchronizationContext";return false;
        }
        auto field=a_.class_get_field_from_name(klass,"m_MainThreadID");
        if(!field || (a_.field_get_flags(field)&0x10) ||
           a_.type_get_type(a_.field_get_type(field))!=0x08) {
            error="Unity main-thread ID field is unavailable or not an instance Int32";return false;
        }
        int32_t mainId{};
        a_.field_get_value(context,field,&mainId);
        auto thread=call(currentThread_,nullptr,nullptr,error);
        if(!thread) return false;
        auto boxed=call(managedThreadId_,thread,nullptr,error);
        if(!boxed) return false;
        auto unboxed=a_.object_unbox(boxed);
        if(!unboxed) { error="Cannot read managed thread ID";return false; }
        int32_t thisId{};std::memcpy(&thisId,unboxed,sizeof(thisId));
        if(mainId<=0 || mainId!=thisId) { error="Caller is not Unity's managed main thread";return false; }
        return true;
    }
    bool verifyDispatcher(std::string& error) override {
        if(dispatcher_) return true;
        auto image=findImage("Assembly-CSharp.dll");
        if(!image) { error="Assembly-CSharp.dll unavailable";return false; }
        auto klass=a_.class_from_name(image,"","GMCmd");
        if(!klass) { error="GMCmd in the expected namespace unavailable";return false; }
        void* iter=nullptr;
        const Method* candidate=nullptr;
        while(auto method=a_.class_get_methods(klass,&iter)) {
            if(std::strcmp(a_.method_get_name(method),"CMDCall")!=0) continue;
            if(candidate) { error="Ambiguous CMDCall overloads; inspection required";return false; }
            candidate=method;
        }
        uint32_t implementationFlags{};
        if(!candidate || a_.method_get_token(candidate)!=0x0600a2c3 ||
           (a_.method_get_flags(candidate,&implementationFlags)&0x10) ||
           a_.method_get_param_count(candidate)!=1 ||
           typeName(a_.method_get_param(candidate,0))!="System.String" ||
           a_.type_get_type(a_.method_get_param(candidate,0))!=0x0e ||
           a_.method_is_generic(candidate) || a_.method_is_inflated(candidate)) {
            error="CMDCall token/instance/string signature mismatch; no invocation attempted";return false;
        }
        returnType_=typeName(a_.method_get_return_type(candidate));
        if(returnType_!="System.Void" && returnType_!="System.Boolean" && returnType_!="System.String") {
            error="CMDCall return type is unsupported: "+returnType_;return false;
        }
        dispatcher_=candidate;
        dispatcherClass_=klass;
        return true;
    }
    Invocation invoke(const std::string& command) override {
        // Called only by Bridge::pump after its thread/signature checks.
        if(!dispatcher_) return {true,"Dispatcher not resolved"};
        if(!dispatcherRoot_) {
            auto object=a_.object_new(dispatcherClass_);
            if(!object) return {true,"GMCmd allocation failed"};
            dispatcherRoot_=a_.gchandle_new(object,false);
            if(!dispatcherRoot_) return {true,"Cannot root GMCmd instance"};
            const Method* ctor=nullptr;void* it=nullptr;
            while(auto m=a_.class_get_methods(dispatcherClass_,&it))
                if(a_.method_get_token(m)==0x0600a2f6 && a_.method_get_param_count(m)==0)ctor=m;
            if(!ctor) {a_.gchandle_free(dispatcherRoot_);dispatcherRoot_=0;return {true,"GMCmd constructor token mismatch"};}
            std::string ctorError;
            call(ctor,a_.gchandle_get_target(dispatcherRoot_),nullptr,ctorError);
            if(!ctorError.empty()) {a_.gchandle_free(dispatcherRoot_);dispatcherRoot_=0;return {true,ctorError};}
        }
        auto str=a_.string_new_len(command.data(),static_cast<uint32_t>(command.size()));
        if(!str) return {true,"Managed string allocation failed"};
        const auto handle=a_.gchandle_new(reinterpret_cast<Object*>(str),false);
        if(!handle) return {true,"GC root allocation failed"};
        struct Root { Api& a;uint32_t h;~Root(){a.gchandle_free(h);} } root{a_,handle};
        auto target=a_.gchandle_get_target(handle);
        if(!target) return {true,"Managed string root unavailable"};
        void* args[]{target}; // Reference-type argument: object pointer, not pointer-to-pointer.
        std::string error;
        auto result=call(dispatcher_,a_.gchandle_get_target(dispatcherRoot_),args,error);
        if(!error.empty()) return {true,error};
        if(returnType_=="System.Boolean") {
            if(!result) return {true,"Null boxed Boolean result from dispatcher"};
            uint8_t value{};auto p=a_.object_unbox(result);
            if(!p) return {true,"Cannot unbox dispatcher result"};
            std::memcpy(&value,p,sizeof(value));
            return {false,std::string("CMDCall returned ")+(value?"true":"false")+
                          "; gameplay effect remains unverified"};
        }
        return {false,"CMDCall returned ("+returnType_+"); gameplay effect remains unverified"};
    }
private:
    std::string typeName(const Type* type) {
        if(!type) return {};
        auto raw=a_.type_get_name(type);
        if(!raw) return {};
        std::string s(raw);a_.free(raw);return s;
    }
    const Image* findImage(const char* name) {
        auto domain=a_.domain_get();if(!domain) return nullptr;
        size_t count{};auto assemblies=a_.domain_get_assemblies(domain,&count);
        if(!assemblies || count>4096) return nullptr;
        for(size_t i=0;i<count;++i) {
            auto image=a_.assembly_get_image(assemblies[i]);
            auto n=image?a_.image_get_name(image):nullptr;
            if(n && std::strcmp(n,name)==0) return image;
        }
        return nullptr;
    }
    Class* findClass(const char* ns,const char* name) {
        auto domain=a_.domain_get();if(!domain) return nullptr;
        size_t count{};auto assemblies=a_.domain_get_assemblies(domain,&count);
        if(!assemblies || count>4096) return nullptr;
        Class* result=nullptr;
        for(size_t i=0;i<count;++i) {
            auto image=a_.assembly_get_image(assemblies[i]);
            auto klass=image?a_.class_from_name(image,ns,name):nullptr;
            if(klass) { if(result && result!=klass) return nullptr;result=klass; }
        }
        return result;
    }
    const Method* getter(Class* klass,const char* name,bool isStatic,const char* returnName) {
        if(!klass) return nullptr;
        void* it=nullptr;const Method* result=nullptr;
        while(auto m=a_.class_get_methods(klass,&it)) {
            uint32_t flags{};
            if(std::strcmp(a_.method_get_name(m),name)==0 && a_.method_get_param_count(m)==0 &&
               bool(a_.method_get_flags(m,&flags)&0x10)==isStatic &&
               typeName(a_.method_get_return_type(m))==returnName) {
                if(result) return nullptr;
                result=m;
            }
        }
        return result;
    }
    bool resolveFramework(std::string& error) {
        if(currentContext_ && currentThread_ && managedThreadId_) return true;
        auto sync=findClass("System.Threading","SynchronizationContext");
        auto thread=findClass("System.Threading","Thread");
        currentContext_=getter(sync,"get_Current",true,"System.Threading.SynchronizationContext");
        currentThread_=getter(thread,"get_CurrentThread",true,"System.Threading.Thread");
        managedThreadId_=getter(thread,"get_ManagedThreadId",false,"System.Int32");
        if(!currentContext_ || !currentThread_ || !managedThreadId_) {
            error="Framework thread/context signatures unavailable";return false;
        }
        return true;
    }
    Object* call(const Method* method,void* instance,void** args,std::string& error) {
        Exception* exception=nullptr;
        auto result=a_.runtime_invoke(method,instance,args,&exception);
        if(exception) {
            auto klass=a_.object_get_class(reinterpret_cast<Object*>(exception));
            char detail[2048]{},stack[4096]{};
            a_.format_exception(exception,detail,sizeof(detail));a_.format_stack_trace(exception,stack,sizeof(stack));
            error="GM bridge operation "+std::string(method?a_.method_get_name(method):"unknown")+": "+
                  std::string(klass?a_.class_get_name(klass):"unknown")+" "+detail+"\n"+stack;
            return nullptr;
        }
        return result;
    }
    Api a_{};
    void* handle_{};
    const Method* currentContext_{},*currentThread_{},*managedThreadId_{},*dispatcher_{};
    std::string returnType_;
    Class* dispatcherClass_{};
    uint32_t dispatcherRoot_{};
};
} // namespace
std::shared_ptr<Backend> makeIl2CppBackend(const std::string& library,
                                         const std::string& metadata,
                                         std::string& error) {
    auto backend=std::make_shared<Il2CppBackend>();
    if(!backend->initialize(library,metadata,error)) return {};
    return backend;
}
} // namespace toi
