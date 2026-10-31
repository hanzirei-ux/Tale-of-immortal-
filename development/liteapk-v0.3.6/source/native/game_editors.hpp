#pragma once
#include "managed_access.hpp"
#include "request_mailbox.hpp"
#include "localization_cache.hpp"
#include <vector>
#include <unordered_set>
namespace toi {
struct EditorContext {Object *player{},*worldData{},*dyn{},*info{},*props{};uint64_t generation{};};
struct EditorResult {std::string state="ERROR",message;bool deferred=false;};
class GameEditors {
    ManagedAccess* m_{};EditorContext c_{};
    Object *store_{},*capacity_{},*catalogOwner_{},*catalogArray_{};
    int bonus_{},catalogCount_{},catalogAt_{};bool capacityReady_{};
    std::chrono::steady_clock::time_point nextBind_{};
    std::string bindingError_,sectScope_,recipeError_;
    std::unordered_set<int> recipeIds_;
    struct Item {int id,type,subtype,level;bool stackable;std::string name,english,chinese,key;};
    std::vector<Item> items_;
    LocalizationCache names_;
    const ManagedMethod *currentLocalize_{},*localize_{},*getCount_{},*rewardMoney_{},*rewardItem_{},*costItem_{};
    bool balance(Object*,int,int&);bool storeBonus(int);bool loadBonus(int&);
    std::string refreshInventory();
    EditorResult currency(const GameRequest&);EditorResult capacity(const GameRequest&);EditorResult catalog(const GameRequest&);
public:
    void initialize(ManagedAccess& m){m_=&m;}
    void bind(const EditorContext&);
    double modifyCapacity(Object*,double)const;
    EditorResult process(const GameRequest&);
    std::string catalogDiagnostics()const{return names_.summary();}
};
}
