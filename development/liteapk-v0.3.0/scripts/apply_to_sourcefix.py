#!/usr/bin/env python3
"""Apply the continuation to the supplied v0.3 SourceFix, never to v0.1/V60.

The original archive is required. No game binary or save is changed by this tool.
The input is SHA-256 pinned; all text changes are prepared before writing.
"""
import argparse
import hashlib
import shutil
import zipfile
from pathlib import Path

SOURCEFIX_SHA256 = '085ecfb13d9c751bcf76c6a5ae5e46d684a8998703a1a259baab6768bdf2cff3'
CHECKPOINT = Path(__file__).resolve().parent.parent

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('SourceFix anchor is missing or ambiguous: ' + old[:100])
    return text.replace(old, new, 1)

def runtime(text):
    text=once(text,'#include "catalog_utils.hpp"','#include "catalog_utils.hpp"\n#include "game_editors.hpp"\n#include "managed_access.hpp"\n#include "request_mailbox.hpp"\n#include <functional>')
    a=text.index('struct Api {');b=text.index('struct Binding',a)
    text=text[:a]+'using Api=ManagedApi;\n'+text[b:]
    text=once(text,'Api a{};uintptr_t','Api a{};ManagedAccess managed{};GameEditors editors{};RequestMailbox mailbox;uintptr_t')
    text=once(text,'std::mutex mutex;std::deque<Request> requests;','std::mutex mutex;')
    a=text.index('    Obj* invoke(');b=text.index('    std::string text(',a)
    text=text[:a]+'''    Obj* invoke(const Method* m,Obj* self=nullptr,void** args=nullptr) {
        auto value=managed.invoke(m,self,args);invokeFailed=managed.failed;
        if(invokeFailed){std::lock_guard<std::mutex> l(mutex);result=managed.error;}
        return value;
    }
'''+text[b:]
    text=once(text,'if(!runtime.isMain()||!runtime.initialized||runtime.failed||!runtime.activeDynMask)return value;','''if(!runtime.isMain()||!runtime.initialized||runtime.failed)return value;
    value=runtime.editors.modifyCapacity(object,value);
    if(!runtime.activeDynMask)return value;''')
    text=once(text,'    LOAD(runtime_invoke);LOAD(string_length);LOAD(string_chars);LOAD(string_new_len);LOAD(array_length);','''    LOAD(runtime_invoke);LOAD(string_length);LOAD(string_chars);LOAD(string_new_len);LOAD(array_length);
    LOAD(class_get_parent);LOAD(field_get_type);LOAD(field_get_flags);LOAD(field_static_get_value);
    LOAD(method_get_token);LOAD(method_get_flags);LOAD(method_get_return_type);LOAD(method_get_class);
    LOAD(type_get_name);LOAD(free);LOAD(object_unbox);LOAD(format_exception);LOAD(format_stack_trace);''')
    text=once(text,'    if(!image)return false;','    if(!image)return false;\n    managed.api=&a;managed.image=image;managed.context="Runtime initialization";editors.initialize(managed);')
    text=once(text,'    process();toi_bridge_pump();','    editors.bind({player,worldData,dyn,unitInfo,read<Obj*>(unitInfo,0x90),generation.load()});\n    process();toi_bridge_pump();')
    a=text.index('    Request q;');b=text.index('    if(q.expiry',a)
    text=text[:a]+'''    GameRequest q;if(!mailbox.pop(q))return;
    bool replied=false;
    auto finish=[this,&q,&replied](std::string s){replied=true;mailbox.finish(q,"RESULT",s);std::lock_guard<std::mutex> l(mutex);result=std::move(s);};
    struct ReplyGuard {std::function<void()> fn;~ReplyGuard(){fn();}} guard{[&]{if(!replied)finish(managed.failed?managed.error:"Operation did not produce a result; no success confirmed");}};
    managed.context=q.kind+" ["+q.key+"]";managed.failed=false;managed.error.clear();
'''+text[b:]
    anchor='    if(q.kind=="gm") {'
    pos=text.index(anchor,text.index('void Runtime::process()'))
    text=text[:pos]+'''    if(q.kind=="currency"||q.kind=="capacity"||q.kind=="catalog"||q.kind=="item") {
        auto reply=editors.process(q);replied=true;
        if(reply.deferred){mailbox.defer(std::move(q));return;}
        mailbox.finish(q,reply.state,reply.message);
        {std::lock_guard<std::mutex> l(mutex);result=reply.state+": "+reply.message;}
        return;
    }
'''+text[pos:]
    a=text.index('    if(q.kind=="capacity") {',text.index('void Runtime::process()'));b=text.index('    finish("Unsupported request");',a)
    text=text[:a]+text[b:]
    text=text.replace('Capacity uses Add Slots (beibao) instead of the capped DynInt setter','Use the persistent Capacity Editor; propGridNum base setter is a no-op')
    text=text.replace('// propGridNum has an engine-defined maximum that can clamp the DynInt setter.\n        // Capacity increases use the native GM `beibao_N` path instead.','// The matching propGridNum base setter is a no-op. Use the Capacity Editor.')
    text=once(text,'bool queueGameRequest(', 'uint64_t queueGameRequest(')
    text=once(text,'&&kind!="capacity"){error=', '&&kind!="capacity"&&kind!="currency"){error=')
    text=once(text,'''if(kind=="capacity" && (key!="slots" || value<1 || value>500 || value!=std::trunc(value))) {
        error="Capacity increment must be whole number 1..500";return false;
    }''','''if((kind=="capacity"||kind=="currency")&&(op< -1||op>2||value<0||value!=std::trunc(value))){error="Use READ, SET, ADD, or SUBTRACT with a non-negative whole amount";return 0;}
    if(kind=="capacity"&&key!="slots"){error="Capacity key rejected";return 0;}''')
    a=text.index('    std::lock_guard<std::mutex> l(runtime.mutex);if(runtime.requests.size()');b=text.index('\n} // namespace toi',a)
    text=text[:a]+'''    auto id=runtime.mailbox.submit(kind,key,op,value,runtime.generation.load());if(!id)error="Queue full";return id;
}
std::string gameRequestResult(){std::lock_guard<std::mutex> l(runtime.mutex);return runtime.result;}
std::vector<GameReply> takeGameRequestResults(){return runtime.mailbox.take();}
void cancelGameRequests(){runtime.mailbox.cancel("Activity closed; action was not executed");std::lock_guard<std::mutex> l(runtime.mutex);runtime.result="CANCELLED: Activity closed";}
'''+text[b:]
    return text

def jni(text):
    anchor='extern "C" JNIEXPORT jboolean JNICALL\nJava_org_npc_toibridge_NativeBridge_controlEnabled'
    text=once(text,anchor,'''extern "C" JNIEXPORT jint JNICALL
Java_org_npc_toibridge_NativeBridge_bridgeVersion(JNIEnv*,jclass){return 3;}
extern "C" JNIEXPORT jstring JNICALL
Java_org_npc_toibridge_NativeBridge_takeGameResults(JNIEnv* env,jclass){
    try{
        std::string json="[";
        for(const auto& r:toi::takeGameRequestResults()){
            if(json.size()>1)json+=",";
            json+="{\\"id\\":"+std::to_string(r.id)+",\\"generation\\":"+std::to_string(r.generation)+
                  ",\\"kind\\":"+quoted(r.kind)+",\\"key\\":"+quoted(r.key)+",\\"state\\":"+quoted(r.state)+",\\"message\\":"+quoted(r.message)+"}";
        }
        return stringResult(env,json+"]");
    }catch(...){return stringResult(env,"[]");}
}
'''+anchor)
    text=once(text,'''auto k=getString(env,kind);if(k!="read"&&k!="catalog"&&backup!=JNI_TRUE)return stringResult(env,"Backup acknowledgment required for persistent edits");''','''auto k=getString(env,kind);bool readOnly=k=="read"||k=="catalog"||((k=="currency"||k=="capacity")&&op==-1);
        if(!readOnly&&backup!=JNI_TRUE)return stringResult(env,"Backup acknowledgment required for persistent edits");''')
    text=once(text,'''return stringResult(env,toi::queueGameRequest(k,getString(env,key),op,value,error)?"QUEUED: waiting for Unity main thread":error);''','''auto id=toi::queueGameRequest(k,getString(env,key),op,value,error);
        return stringResult(env,id?"QUEUED:"+std::to_string(id):error);''')
    return text

def transform(project):
    # Compute ALL outputs before writing any integration changes.
    root=Path(project);java=Path('android/bridge/src/main/java/org/npc/toibridge')
    outputs={}
    outputs['native/game_runtime.cpp']=runtime((root/'native/game_runtime.cpp').read_text())
    header=(root/'native/game_runtime.hpp').read_text()
    header=once(header,'#include "modifiers.hpp"','#include "modifiers.hpp"\n#include "request_mailbox.hpp"')
    header=once(header,'bool queueGameRequest(','uint64_t queueGameRequest(')
    outputs['native/game_runtime.hpp']=once(header,'std::string gameRequestResult();','std::string gameRequestResult();\nstd::vector<GameReply> takeGameRequestResults();')
    outputs['native/jni.cpp']=jni((root/'native/jni.cpp').read_text())
    bridge=(root/java/'NativeBridge.java').read_text()
    outputs[str(java/'NativeBridge.java')]=once(bridge,'    static { System.loadLibrary("toimodmenu"); }','    static { System.loadLibrary("toimodmenu"); }\n    public static native int bridgeVersion();\n    public static native String takeGameResults();')
    import java_changes
    outputs[str(java/'ModMenu.java')]=java_changes.update((root/java/'ModMenu.java').read_text())
    outputs['CMakeLists.txt']=once((root/'CMakeLists.txt').read_text(),'native/jni.cpp native/mod_api.cpp native/game_runtime.cpp)','native/jni.cpp native/mod_api.cpp native/game_runtime.cpp native/managed_access.cpp native/game_editors.cpp)')
    return outputs

def main():
    p=argparse.ArgumentParser();p.add_argument('--sourcefix',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
    if hashlib.sha256(a.sourcefix.read_bytes()).hexdigest()!=SOURCEFIX_SHA256:raise SystemExit('Wrong SourceFix archive hash; input not modified')
    if a.destination.exists():raise SystemExit('Destination must not exist; preserve previous source/build files')
    with zipfile.ZipFile(a.sourcefix) as z:
        for i in z.infolist():
            path=Path(i.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in i.filename:raise SystemExit('Unsafe archive member')
        if z.testzip():raise SystemExit('Archive CRC check failed')
        z.extractall(a.destination)
    candidates=[path.parent for path in a.destination.rglob('CMakeLists.txt') if (path.parent/'native/game_runtime.cpp').is_file()]
    if len(candidates)!=1:raise SystemExit('Expected exactly one existing v0.3 project')
    project=candidates[0]
    try:outputs=transform(project)
    except Exception:
        shutil.rmtree(a.destination);raise
    for relative,text in outputs.items():(project/relative).write_text(text)
    for path in (CHECKPOINT/'overlay').rglob('*'):
        if path.is_file():
            dest=project/path.relative_to(CHECKPOINT/'overlay');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    print('Applied continuation to',project)
    print('Build both ARM64 library and helper DEX before packaging; no device verification claimed.')
if __name__=='__main__':main()
