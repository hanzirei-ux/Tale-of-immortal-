#pragma once
#include <chrono>
#include <cstdint>
#include <deque>
#include <mutex>
#include <string>
#include <vector>
namespace toi {
struct GameRequest {
    uint64_t id{},generation{};std::string kind,key;int op{};double value{};
    std::chrono::steady_clock::time_point expiry;
};
struct GameReply {uint64_t id{},generation{};std::string kind,key,state,message;};
// One receipt per request: browsing cannot overwrite a persistent edit result.
class RequestMailbox {
    mutable std::mutex mutex_;uint64_t next_{1};
    std::deque<GameRequest> pending_;std::deque<GameReply> replies_;
    void finishLocked(GameReply reply){if(replies_.size()==64)replies_.pop_front();replies_.push_back(std::move(reply));}
public:
    using Clock=std::chrono::steady_clock;
    uint64_t submit(std::string kind,std::string key,int op,double value,uint64_t generation,Clock::time_point now=Clock::now()){
        std::lock_guard<std::mutex> l(mutex_);if(pending_.size()>=32||replies_.size()>=32)return 0;
        auto id=next_++;pending_.push_back({id,generation,std::move(kind),std::move(key),op,value,now+std::chrono::seconds(10)});return id;
    }
    bool pop(GameRequest& q){std::lock_guard<std::mutex> l(mutex_);if(pending_.empty())return false;q=std::move(pending_.front());pending_.pop_front();return true;}
    void defer(GameRequest q){std::lock_guard<std::mutex> l(mutex_);if(pending_.size()>=32){finishLocked({q.id,q.generation,q.kind,q.key,"CANCELLED","Queue full while indexing; action was not executed"});return;}pending_.push_back(std::move(q));}
    void finish(const GameRequest& q,std::string state,std::string message){std::lock_guard<std::mutex> l(mutex_);finishLocked({q.id,q.generation,q.kind,q.key,std::move(state),std::move(message)});}
    std::vector<GameReply> take(){std::lock_guard<std::mutex> l(mutex_);std::vector<GameReply> out;while(!replies_.empty()){out.push_back(std::move(replies_.front()));replies_.pop_front();}return out;}
    void cancel(const std::string& reason){std::lock_guard<std::mutex> l(mutex_);while(!pending_.empty()){auto& q=pending_.front();finishLocked({q.id,q.generation,q.kind,q.key,"CANCELLED",reason});pending_.pop_front();}}
};
}
