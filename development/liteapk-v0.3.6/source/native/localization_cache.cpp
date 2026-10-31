#include "localization_cache.hpp"
namespace toi {
TextLookup LocalizationCache::lookup(const std::string& key,int language,const std::function<TextLookup(int)>& callback){
    const size_t slot=language<0?0:language==2?1:language==0?2:language==1?3:4;
    auto& cache=memo_[key];if(cache.present[slot])return cache.values[slot];
    auto result=callback(language);
    if(result.state==LookupState::Found&&(result.text.empty()||result.text==key))result.state=LookupState::Missing;
    if(result.state==LookupState::Fatal)return result;
    cache.values[slot]=result;cache.present[slot]=true;
    if(result.state==LookupState::Missing){++missingLookups_;if(missing_.insert(key).second&&samples_.size()<16)samples_.push_back(key);}
    return result;
}
CatalogName LocalizationCache::resolve(const std::string& key,int id,const std::function<TextLookup(int)>& callback){
    CatalogName out;out.key=key;
    if(key.empty()){out.display="#"+std::to_string(id);out.fallback=true;++fallbackItems_;return out;}
    for(int language:{-1,2,0}){
        auto value=lookup(key,language,callback);
        if(value.state==LookupState::Fatal){out.failed=true;out.error=value.error;return out;}
        if(value.state==LookupState::Found){if(language==-1)out.current=value.text;else if(language==2)out.english=value.text;else out.chinese=value.text;}
    }
    out.display=!out.current.empty()?out.current:!out.english.empty()?out.english:out.chinese;
    if(out.display.empty())for(int language:{1,3}){auto value=lookup(key,language,callback);if(value.state==LookupState::Fatal){out.failed=true;out.error=value.error;return out;}if(value.state==LookupState::Found){out.display=value.text;break;}}
    if(out.display.empty()){out.display=key;out.fallback=true;++fallbackItems_;}
    return out;
}
std::string LocalizationCache::summary()const{
    std::string s="Localization: missing keys="+std::to_string(missing_.size())+", missing language lookups="+std::to_string(missingLookups_)+", internal-key fallbacks="+std::to_string(fallbackItems_);
    if(!samples_.empty()){s+="; examples: ";for(size_t i=0;i<samples_.size();++i){if(i)s+=", ";s+=samples_[i];}}
    return s;
}
}
