#include "game_editors.hpp"
#include "editor_math.hpp"
#include "catalog_utils.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <sstream>
namespace toi {
namespace {
using M=MethodSpec;
// Tokens are references checked with the live signature, never executable addresses.
const M getConf{"get_conf",0x06000070,"ConfMgr",{},true};
const M getUI{"get_ui",0x06000073,"UIMgr",{},true};
const M itemConf{"get_itemProps",0x060004d4,"ConfItemProps",{}};
const M itemList{"get_allConfList",0x060059e4,"$ref",{}};
const M recipeConf{"get_makePillFormula",0x0600044f,"ConfMakePillFormula",{}};
const M recipeList{"get_allConfList",0x06005ac3,"$ref",{}};
const M localized{"GetText",0x06004698,"System.String",{"System.String","LanguageType"},true};
const M getNum{"GetPropsNum",0x060084fb,"System.Int32",{"System.Int32"}};
const M moneyReward{"RewardPropMoney",0x06015a8e,"System.Void",{"System.Int32"}};
const M itemReward{"RewardPropItem",0x06015a8f,"System.Void",{"System.Int32","System.Int32","System.Boolean"}};
const M itemCost{"CostPropItem",0x06015a96,"System.Void",{"System.Int32","System.Int32","System.Boolean"}};
const M gridMax{"GetGridMaxNum",0x06008772,"System.Int32",{}};
const M gridUsed{"GetGridCurNum",0x06008774,"System.Int32",{}};
const M setStored{"SetString",0x060086fe,"System.Void",{"System.String","System.Int32"}};
const M getStored{"GetInt",0x06008703,"System.Int32",{"System.String","System.Int32"}};
const M getSchool{"get_school",0x06015a77,"MapBuildSchool",{}};
const M schoolData{"get_buildData",0x06012c7b,"DataBuildSchool.SchoolData",{}};
const M schoolName{"get_name",0x06012c75,"System.String",{}};
const M addFunds{"AddMoney",0x0600863f,"System.Void",{"System.Int64"}};
const M addReputation{"AddReputation",0x06008640,"System.Void",{"System.Int32"}};
const M addFaith{"AddFaithMoney",0x06008641,"System.Void",{"System.Int64"}};
const M findUI{"GetUI",0x06000c15,"$ref",{"UIType.UITypeBase"}};
const M bagOwner{"get_unit",0x06010707,"WorldUnitBase",{}};
const M bagUpdate{"UpdateUI",0x06010717,"System.Void",{}};
const M switchPropUpdate{"UpdateUI",0x06011bd9,"System.Void",{"System.Boolean"}};
const M dynEffective{"get_value",0x06015f05,"System.Int32",{}};
const M propUpdate{"UpdateUI",0x0601094b,"System.Void",{"System.Boolean"}};
constexpr const char* capacityKey="toimodmenu.v03.capacityBonus";
template<class T>T at(Object* o,size_t n){T v{};if(o)std::memcpy(&v,static_cast<char*>(o)+n,sizeof(v));return v;}
EditorResult error(ManagedAccess& m,const char* fallback){return {"BLOCKED",m.failed?m.error:fallback,false};}
}
bool GameEditors::loadBonus(int& out){auto& m=*m_;auto key=m.string(capacityKey);int def=0;void* args[]{key,&def};return m.intResult(m.objectMethod(store_,getStored),store_,args,out);}
bool GameEditors::storeBonus(int value){auto& m=*m_;auto key=m.string(capacityKey);void* args[]{key,&value};m.invoke(m.objectMethod(store_,setStored),store_,args);return !m.failed;}
void GameEditors::bind(const EditorContext& next){
    if(!m_)return;
    bool changed=next.player!=c_.player||next.dyn!=c_.dyn||next.info!=c_.info||next.props!=c_.props||next.generation!=c_.generation;
    c_=next;auto now=std::chrono::steady_clock::now();
    if(!changed&&(capacityReady_||now<nextBind_))return;
    nextBind_=now+std::chrono::seconds(1);
    capacityReady_=false;capacity_=nullptr;store_=nullptr;bonus_=0;if(changed)sectScope_.clear();
    auto& m=*m_;m.context="Capacity initialization";m.failed=false;
    if(!c_.player||!c_.info||!c_.dyn||!c_.props){bindingError_="Player inventory/save is not initialized";return;}
    capacity_=m.objectField(c_.dyn,"propGridNum","DynInt");store_=m.objectField(c_.info,"objData","DataObjectData");int saved{};
    if(m.failed||!capacity_||!store_||!loadBonus(saved)){bindingError_=m.failed?m.error:"Player save object store is not initialized";return;}
    if(saved< -2000||saved>2000){bindingError_="Saved capacity bonus outside supported range; unchanged";return;}
    bonus_=saved;capacityReady_=true;bindingError_.clear();
}
double GameEditors::modifyCapacity(Object* object,double value)const{return capacityReady_&&bonus_&&object==capacity_?std::clamp(value+bonus_,1.0,2000000000.0):value;}
bool GameEditors::balance(Object* props,int id,int& out){auto& m=*m_;if(!getCount_)getCount_=m.objectMethod(props,getNum);void* args[]{&id};return m.intResult(getCount_,props,args,out);}
std::string GameEditors::refreshInventory(){
    auto& m=*m_;m.context="Inventory UI refresh";
    auto mgr=m.invoke(m.method(m.klass("g"),getUI));if(m.failed)return m.error;if(!mgr)return "Inventory UI not open; reopen bag to refresh";
    auto get=m.objectMethod(mgr,findUI);if(!get)return "Inventory UI method unavailable; reopen bag";auto uiType=m.klass("UIType");
    for(auto name:{"PlayerBagExtend","PlayerInfo","SwitchPlayerInfoBag"}){
        auto f=uiType?m.api->class_get_field_from_name(uiType,name):nullptr;if(!f)continue;
        Object* type=nullptr;m.api->field_static_get_value(f,&type);if(!type)continue;void* args[]{type};
        auto ui=m.invoke(get,mgr,args);if(m.failed)return m.error;if(!ui)continue;
        if(std::strcmp(name,"PlayerBagExtend")==0){auto owner=m.invoke(m.objectMethod(ui,bagOwner),ui);if(m.failed)return m.error;if(owner==c_.player)m.invoke(m.objectMethod(ui,bagUpdate),ui);}
        else{auto owner=m.objectField(ui,"unit");if(m.failed)return m.error;if(owner==c_.player){auto prop=m.objectField(ui,"uiProp");if(prop){bool anim=false;void* a[]{&anim};m.invoke(m.objectMethod(prop,std::strcmp(name,"SwitchPlayerInfoBag")==0?switchPropUpdate:propUpdate),prop,a);}}}
        if(m.failed)return m.error;
    }
    return "Open inventory views refreshed; reopen other bag screens if needed";
}
EditorResult GameEditors::capacity(const GameRequest& q){
    auto& m=*m_;m.context="Inventory Capacity";if(!capacityReady_)return {"BLOCKED",bindingError_,false};int before{},used{};
    if(!m.intResult(m.objectMethod(c_.props,gridMax),c_.props,nullptr,before)||!m.intResult(m.objectMethod(c_.props,gridUsed),c_.props,nullptr,used))return error(m,"Capacity cannot be read");
    auto summary=[&](int n){return "Effective capacity="+std::to_string(n)+", occupied="+std::to_string(used)+", saved player bonus="+std::to_string(bonus_);};
    if(q.op==-1)return {"READ",summary(before),false};
    const ManagedMethod* getter=m.objectMethod(capacity_,dynEffective);
    int now{};if(!m.intResult(getter,capacity_,nullptr,now))return error(m,"Capacity DynInt unavailable");
    int factor=now>0&&before%now==0?before/now:0;AmountPlan plan;int next{};std::string why;
    if(!planCapacity(before,used,factor,bonus_,q.op,q.value,plan,next,why))return {"REJECTED",why,false};
    if(!plan.delta)return {"UNCHANGED",summary(before)+"; requested amount already matches",false};
    int old=bonus_;bool wrote=storeBonus(next);auto warning=m.failed?m.error:"";int stored{};
    if(!loadBonus(stored))return error(m,"Cannot verify saved bonus; do not retry before READ");
    if(stored!=next)return {"FAILED","Capacity storage did not change; "+summary(before)+"; "+warning,false};
    bonus_=stored;int after{};bool readAfter=m.intResult(m.objectMethod(c_.props,gridMax),c_.props,nullptr,after);
    if(!readAfter||after!=plan.target){
        auto fault=m.error;bool restored=storeBonus(old);int check{};restored=restored&&loadBonus(check)&&check==old;if(restored)bonus_=old;
        return {"FAILED","Capacity readback mismatch; "+std::string(restored?"previous bonus restored":"RESTORE FAILED; use READ before further edits")+". "+fault,false};
    }
    auto refresh=refreshInventory();bool warn=!wrote||refresh.find("MANAGED_EXCEPTION")!=std::string::npos;
    return {warn?"APPLIED_WITH_WARNING":"APPLIED","Capacity: "+std::to_string(before)+" -> "+std::to_string(after)+" (occupied "+std::to_string(used)+"). "+refresh+". Player objData updated; save/load needs phone test. "+warning,false};
}
EditorResult GameEditors::currency(const GameRequest& q){
    auto& m=*m_;m.context="Currency "+q.key;bool sect=q.key.rfind("sect_",0)==0;
    Object* target=c_.props;std::string scope="Player";int64_t before{};int fieldType=8;const char* field=nullptr;const M* mutator=nullptr;int id{};
    if(sect){
        auto school=m.invoke(m.objectMethod(c_.worldData,getSchool),c_.worldData);if(m.failed)return error(m,"");if(!school)return {"BLOCKED","Player is not in an initialized sect",false};
        auto sid=m.text(m.objectField(c_.info,"schoolID","System.String"));auto name=m.text(m.invoke(m.objectMethod(school,schoolName),school));if(m.failed)return error(m,"");
        target=m.invoke(m.objectMethod(school,schoolData),school);if(m.failed||!target||sid.empty())return error(m,"Player sect data is not ready");scope="Player sect: "+name+" ["+sid+"]";
        if(q.op==-1)sectScope_=sid;else if(sectScope_!=sid)return {"REJECTED","READ this sect resource first; player's sect changed or was not confirmed",false};
        if(q.key=="sect_funds"){field="money";fieldType=10;mutator=&addFunds;}
        else if(q.key=="sect_reputation"){field="reputation";mutator=&addReputation;}
        else if(q.key=="sect_faith"){field="faithMoney";fieldType=10;mutator=&addFaith;}
        else return {"REJECTED","Unknown sect resource",false};
        if(!m.integerField(target,field,before,fieldType))return error(m,"");
    }else{
        const char* owner="PropsIDType";const char* constant=nullptr;int expected{};
        if(q.key=="money"){constant="Money";expected=10001;}
        else if(q.key=="contribution"){constant="SchoolMoney";expected=10011;}
        else if(q.key=="city_token"){constant="CityToken";expected=10041;}
        else if(q.key=="immortal_token"){owner="UIImmortalStore";constant="TokenPropID";expected=10051;}
        else return {"REJECTED","Unknown personal currency",false};
        if(!m.constant(owner,constant,id)||id!=expected)return error(m,"Currency identifier mismatch");
        if(q.key=="contribution"&&m.text(m.objectField(c_.info,"schoolID")).empty())return {"BLOCKED","Join a sect before editing personal contribution",false};
        int value{};if(!balance(target,id,value))return error(m,"");before=value;scope+=" currency item #"+std::to_string(id);
    }
    if(q.op==-1)return {"READ",scope+"\nCurrent: "+std::to_string(before),false};
    AmountPlan plan;std::string why;auto maximum=fieldType==10?1000000000000LL:2000000000LL;
    if(!planAmount(before,q.op,q.value,maximum,plan,why))return {"REJECTED",why,false};
    if(!plan.delta)return {"UNCHANGED",scope+": "+std::to_string(before)+" (already matches)",false};
    if(q.key=="contribution"&&plan.delta>0){
        int64_t lifetime{};if(!m.integerField(c_.props,"totalSchoolMoney",lifetime))return error(m,"");
        if(lifetime<0||lifetime>2147483647LL-plan.delta)return {"REJECTED","Native contribution lifetime counter would overflow; no balance change attempted",false};
    }
    if(sect){int64_t d=plan.delta;int d32=fieldType==8?int(plan.delta):0;void* args[]{fieldType==10?static_cast<void*>(&d):static_cast<void*>(&d32)};m.invoke(m.objectMethod(target,*mutator),target,args);}
    else{
        if(!rewardMoney_)rewardMoney_=m.objectMethod(c_.worldData,moneyReward);
        if(!rewardItem_)rewardItem_=m.objectMethod(c_.worldData,itemReward);
        if(!costItem_)costItem_=m.objectMethod(c_.worldData,itemCost);
        int amount=int(std::abs(plan.delta));bool show=false;
        if(plan.delta>0&&q.key=="money"){void* args[]{&amount};m.invoke(rewardMoney_,c_.worldData,args);}
        else{void* args[]{&id,&amount,&show};m.invoke(plan.delta>0?rewardItem_:costItem_,c_.worldData,args);}
    }
    // The original sect methods can throw during UI refresh AFTER committing.
    // Preserve the exception, read actual state, and never silently retry.
    auto mutationError=m.failed?m.error:"";int64_t after{};
    if(sect){if(!m.integerField(target,field,after,fieldType))return {"FAILED","Mutation attempted; readback failed. Do not retry before READ. "+mutationError+" "+m.error,false};}
    else{int value{};if(!balance(target,id,value))return {"FAILED","Mutation attempted; readback failed. Do not retry before READ. "+mutationError+" "+m.error,false};after=value;}
    auto summary=scope+"\n"+std::to_string(before)+" -> "+std::to_string(after)+" (requested "+std::to_string(plan.target)+")";
    if(after!=plan.target)return {"FAILED",summary+"; actual value differs. READ before retry. "+mutationError,false};
    return {mutationError.empty()?"APPLIED":"APPLIED_WITH_WARNING",summary+"\nSave/load not device tested. "+mutationError,false};
}
EditorResult GameEditors::catalog(const GameRequest& q){
    auto& m=*m_;m.context=q.kind=="item"?"Add selected item":"Item catalog";
    auto conf=m.invoke(m.method(m.klass("g"),getConf));if(m.failed||!conf)return error(m,"Game configuration not initialized");
    auto owner=m.invoke(m.objectMethod(conf,itemConf),conf);if(m.failed||!owner)return error(m,"Item database not initialized");
    if(owner!=catalogOwner_){
        auto list=m.invoke(m.objectMethod(owner,itemList),owner);if(m.failed||!m.list(list,catalogArray_,catalogCount_))return error(m,"Item catalog list is not ready");
        auto cls=m.klass("ConfItemPropsItem");
        for(auto pair:{std::pair<const char*,size_t>{"id",0x10},{"name",0x18},{"type",0x20},{"className",0x24},{"hide",0x28},{"level",0x40},{"isOverlay",0x50}}){auto f=cls?m.api->class_get_field_from_name(cls,pair.first):nullptr;if(!f||m.api->field_get_offset(f)!=pair.second)return {"BLOCKED","Item configuration field layout mismatch",false};}
        catalogOwner_=owner;catalogAt_=0;items_.clear();items_.reserve(size_t(catalogCount_));localize_=m.method(m.klass("ConfLocalText"),localized);
        recipeIds_.clear();recipeError_.clear();
        // Native AddPillFormulaOptions looks up makePillFormula by propsItem.id.
        // Classify the intersection of real recipe IDs with the real item catalog.
        auto recipes=m.invoke(m.objectMethod(conf,recipeConf),conf);
        auto recipeRows=recipes?m.invoke(m.objectMethod(recipes,recipeList),recipes):nullptr;
        Object* recipeArray=nullptr;int recipeCount{};
        if(!m.failed&&m.list(recipeRows,recipeArray,recipeCount)&&recipeCount<=10000){
            for(int i=0;i<recipeCount;++i){auto item=at<Object*>(recipeArray,32+size_t(i)*sizeof(void*));int64_t id{};
                if(!m.integerField(item,"id",id)){recipeIds_.clear();break;}if(id>0&&id<=2000000000)recipeIds_.insert(int(id));
            }
        }else if(!m.failed)m.reject("Recipe configuration missing or exceeds this build's bound");
        if(m.failed){recipeError_=m.error;m.failed=false;m.error.clear();}
    }
    auto until=std::chrono::steady_clock::now()+std::chrono::milliseconds(3);int batch=0;
    while(catalogAt_<catalogCount_&&batch<128){
        auto item=at<Object*>(catalogArray_,32+size_t(catalogAt_++)*sizeof(void*));++batch;if(!item||at<int>(item,0x28)!=0)continue;
        auto keyObj=at<Object*>(item,0x18);auto key=m.text(keyObj);std::string en,ch;
        if(keyObj&&localize_){int lang=2;void* args[]{keyObj,&lang};en=m.text(m.invoke(localize_,nullptr,args));if(m.failed)return error(m,"");lang=0;ch=m.text(m.invoke(localize_,nullptr,args));if(m.failed)return error(m,"");}
        auto useful=[&](const std::string& v){return !v.empty()&&v!=key;};auto name=useful(en)?en:useful(ch)?ch:key;
        items_.push_back({at<int>(item,0x10),at<int>(item,0x20),at<int>(item,0x24),at<int>(item,0x40),at<int>(item,0x50)!=0,name,en,ch,key});
        if(batch>=8&&std::chrono::steady_clock::now()>=until)break;
    }
    if(catalogAt_<catalogCount_)return {"INDEXING","Localized item catalog",true};
    if(q.kind=="item"){
        int id{};try{size_t used{};id=std::stoi(q.key,&used);if(used!=q.key.size())return {"REJECTED","Invalid decimal item ID",false};}catch(...){return {"REJECTED","Invalid item ID",false};}
        auto item=std::find_if(items_.begin(),items_.end(),[&](const Item& i){return i.id==id;});
        if(item==items_.end()||q.value<1||q.value>9999||q.value!=std::trunc(q.value))return {"REJECTED","Unknown item or quantity outside 1..9999",false};
        if(!item->stackable&&q.value>1)return {"REJECTED","Non-stackable item: add one per request",false};
        int before{};if(!balance(c_.props,id,before))return error(m,"");if(before>2000000000-int(q.value))return {"REJECTED","Item count overflow guard",false};
        int count=int(q.value);bool show=false;void* args[]{&id,&count,&show};m.invoke(m.objectMethod(c_.worldData,itemReward),c_.worldData,args);auto warning=m.failed?m.error:"";
        int after{};if(!balance(c_.props,id,after))return error(m,"Item mutation attempted; READ inventory before retry");
        return {after==before+count?(warning.empty()?"APPLIED":"APPLIED_WITH_WARNING"):"FAILED",item->name+" (#"+std::to_string(id)+"): "+std::to_string(before)+" -> "+std::to_string(after)+". "+warning,false};
    }
    CatalogQuery query;if(!parseCatalogQuery(q.key,query))return {"REJECTED","Invalid catalog query",false};if(query.type==254&&!recipeError_.empty())return {"BLOCKED",recipeError_,false};
    int total=0,shown=0;std::ostringstream rows;
    for(int pass=0;pass<(query.term.empty()?1:2);++pass)for(const auto& item:items_){
        if(query.type==254){if(!recipeIds_.count(item.id))continue;}
        else if(query.type!=-1&&query.type!=item.type)continue;
        int rank=-1;
        for(const auto* name:{&item.english,&item.chinese,&item.key}){auto r=matchRank(*name,std::to_string(item.id),query.term);if(r>=0&&(rank<0||r<rank))rank=r;}
        if(rank!=pass)continue;
        if(total>=query.offset&&shown<40){rows<<item.id<<'\t'<<safeCatalogName(item.name)<<'\t'<<item.type<<'\t'<<item.level<<'\n';++shown;}++total;
    }
    return {"CATALOG","CATALOG\t"+std::to_string(total)+"\t"+std::to_string(query.offset)+"\t40\n"+rows.str(),false};
}
EditorResult GameEditors::process(const GameRequest& q){
    if(!m_)return {"BLOCKED","Editor integration not initialized",false};
    auto& m=*m_;m.failed=false;m.error.clear();
    if(!c_.player||!c_.worldData||!c_.info||!c_.props||!m.objectField(c_.props,"allProps"))return error(m,"Load a player save before this operation");
    if(q.kind=="currency")return currency(q);
    if(q.kind=="capacity")return capacity(q);
    if(q.kind=="catalog"||q.kind=="item")return catalog(q);
    return {"REJECTED","Unknown editor request",false};
}
}
