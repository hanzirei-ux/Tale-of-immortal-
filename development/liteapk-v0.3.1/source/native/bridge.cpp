#include "bridge.hpp"
#include <algorithm>

namespace toi {
bool makeProbeCommand(Action action, int64_t value, std::string& command,
                      std::string& reason) {
    command.clear();
    if (action == Action::AddExpProbe && value >= 1 && value <= 100) {
        command = "jingyan_" + std::to_string(value);
        return true;
    }
    if (action == Action::AddHpProbe && value >= 1 && value <= 10) {
        command = "shuxing_hp_" + std::to_string(value);
        return true;
    }
    reason = action == Action::AddItem
        ? "BLOCKED: item parameter layout and real item IDs are not verified"
        : "Rejected: EXP probe accepts 1..100; HP probe accepts 1..10";
    return false;
}
Bridge::Bridge(std::shared_ptr<Backend> backend) : backend_(std::move(backend)) {}
void Bridge::recordLocked(Receipt receipt) {
    if (results_.size() == 64) results_.pop_front();
    results_.push_back(std::move(receipt));
}
void Bridge::cancelLocked(const std::string& state, const std::string& reason) {
    for (const auto& r : pending_) recordLocked({r.id, state, reason});
    pending_.clear();
}
bool Bridge::arm(const std::string& session, bool backup, bool experimental,
                 std::string& error) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!backend_ || !backup || !experimental || session.empty() || session.size() > 64 ||
        !std::all_of(session.begin(), session.end(), [](unsigned char c) {
            return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                   (c >= '0' && c <= '9') || c == '-';
        })) {
        error = "BLOCKED: verified baseline, backup, experiment acknowledgment and session ID required";
        return false;
    }
    cancelLocked("CANCELLED", "New experimental session");
    ++epoch_;
    session_ = session;
    armed_ = true;
    status_ = "ARMED — NOT VERIFIED: waiting for a verified Unity main-thread callback";
    return true;
}
Receipt Bridge::enqueue(Action action, int64_t value, const std::string& session,
                        Clock::time_point now) {
    std::lock_guard<std::mutex> lock(mutex_);
    Receipt r{nextId_++, "REJECTED", {}};
    std::string command;
    if (!makeProbeCommand(action, value, command, r.detail)) return r;
    if (!armed_ || session != session_) {
        r.detail = "Bridge disabled or world session changed";
        return r;
    }
    if (pending_.size() >= 32) { r.detail = "Command queue full"; return r; }
    pending_.push_back({r.id, epoch_, std::move(command), now + std::chrono::seconds(10)});
    r.state = "QUEUED";
    r.detail = "Awaiting Unity thread; game state has not been verified";
    return r;
}
void Bridge::disarm(const std::string& reason) {
    std::lock_guard<std::mutex> lock(mutex_);
    armed_ = false;
    ++epoch_;
    session_.clear();
    cancelLocked("CANCELLED", reason);
    status_ = "DISABLED: " + reason;
}
void Bridge::pump(Clock::time_point now) {
    if (pumping_.test_and_set()) return; // no recursion, no simultaneous dispatch
    struct Guard { std::atomic_flag& f; ~Guard() { f.clear(); } } guard{pumping_};
    Request request;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!armed_ || pending_.empty() || !backend_) return;
        request = std::move(pending_.front());
        pending_.pop_front();
        if (request.deadline <= now) {
            recordLocked({request.id, "EXPIRED", "No command executed; queue lifetime exceeded"});
            return;
        }
    }
    try {
    std::string reason;
    if (!backend_->verifyMainThread(reason) || !backend_->verifyDispatcher(reason)) {
        std::lock_guard<std::mutex> lock(mutex_);
        armed_ = false;
        ++epoch_;
        recordLocked({request.id, "BLOCKED", reason});
        cancelLocked("CANCELLED", reason);
        status_ = "BLOCKED: " + reason;
        return;
    }
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!armed_ || epoch_ != request.epoch) {
            recordLocked({request.id, "CANCELLED", "Disabled before invocation"});
            return;
        }
    }
    // Disabling cancels queued operations; an already entered managed call cannot
    // be rolled back. No locks are held while the game runs.
    auto result = backend_->invoke(request.command);
    std::lock_guard<std::mutex> lock(mutex_);
    recordLocked({request.id, result.exception ? "MANAGED_EXCEPTION" : "INVOKED_UNVERIFIED",
                  std::move(result.detail)});
    status_ = result.exception ? "BLOCKED: managed exception; re-arm required"
                              : "INVOKED_UNVERIFIED: inspect actual game state";
    if (result.exception) {
        armed_ = false;
        ++epoch_;
        cancelLocked("CANCELLED", "Managed exception");
    }
    } catch (...) {
        std::lock_guard<std::mutex> lock(mutex_);
        armed_ = false;
        ++epoch_;
        recordLocked({request.id, "NATIVE_EXCEPTION", "Native C++ boundary failed; no automatic retry"});
        cancelLocked("CANCELLED", "Native C++ exception");
        status_ = "BLOCKED: native C++ exception; re-arm required";
    }
}
std::vector<Receipt> Bridge::takeReceipts() {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<Receipt> result(results_.begin(), results_.end());
    results_.clear();
    return result;
}
std::string Bridge::status() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return status_;
}
} // namespace toi
