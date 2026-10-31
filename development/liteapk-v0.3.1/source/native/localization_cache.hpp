#pragma once
#include <array>
#include <functional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
namespace toi {
enum class LookupState {Found,Missing,Fatal};
struct TextLookup {LookupState state=LookupState::Missing;std::string text,error;};
struct CatalogName {std::string display,current,english,chinese,key,error;bool fallback{},failed{};};
// The callback must classify only the exact expected managed missing-key exception
// as Missing. Fatal errors are not cached or suppressed.
class LocalizationCache {
    struct Memo {std::array<TextLookup,5> values;std::array<bool,5> present{};};
    std::unordered_map<std::string,Memo> memo_;
    std::unordered_set<std::string> missing_;
    std::vector<std::string> samples_;
    size_t missingLookups_{},fallbackItems_{};
    TextLookup lookup(const std::string&,int,const std::function<TextLookup(int)>&);
public:
    CatalogName resolve(const std::string& key,int id,const std::function<TextLookup(int)>&);
    void clear(){memo_.clear();missing_.clear();samples_.clear();missingLookups_=fallbackItems_=0;}
    size_t missingKeys()const{return missing_.size();}
    size_t missingLookups()const{return missingLookups_;}
    size_t fallbackItems()const{return fallbackItems_;}
    const std::vector<std::string>& samples()const{return samples_;}
    std::string summary()const;
};
}
