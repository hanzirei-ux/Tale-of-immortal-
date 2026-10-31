#pragma once
#include <atomic>
#include <chrono>
#include <cstdint>
#include <deque>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace toi {
// These are bounded research probes, not verified gameplay features.
enum class Action { AddExpProbe, AddHpProbe, AddItem };
struct Receipt {
    uint64_t id{};
    std::string state, detail;
};
struct Invocation { bool exception{}; std::string detail; };
class Backend {
public:
    virtual ~Backend() = default;
    virtual bool verifyMainThread(std::string& reason) = 0;
    virtual bool verifyDispatcher(std::string& reason) = 0;
    virtual Invocation invoke(const std::string& command) = 0;
};
// Production construction is only through makeIl2CppBackend, which checks hashes
// and the loaded library's identity. Tests inject a fake Backend explicitly.
std::shared_ptr<Backend> makeIl2CppBackend(const std::string& library,
                                         const std::string& metadata,
                                         std::string& error);
bool makeProbeCommand(Action action, int64_t value, std::string& command,
                      std::string& reason);
class Bridge final {
public:
    using Clock = std::chrono::steady_clock;
    explicit Bridge(std::shared_ptr<Backend> backend);
    bool arm(const std::string& worldSession, bool backupAcknowledged,
             bool experimentalAcknowledged, std::string& error);
    Receipt enqueue(Action action, int64_t value, const std::string& worldSession,
                    Clock::time_point now = Clock::now());
    void pump(Clock::time_point now = Clock::now()); // verified Unity callback ONLY
    void disarm(const std::string& reason = "Disabled by caller");
    std::vector<Receipt> takeReceipts();
    std::string status() const;
private:
    struct Request {
        uint64_t id, epoch;
        std::string command;
        Clock::time_point deadline;
    };
    void recordLocked(Receipt receipt);
    void cancelLocked(const std::string& state, const std::string& reason);
    std::shared_ptr<Backend> backend_;
    mutable std::mutex mutex_;
    std::deque<Request> pending_;
    std::deque<Receipt> results_;
    uint64_t nextId_{1}, epoch_{0};
    bool armed_{false};
    std::string session_, status_{"BLOCKED: not armed; Unity adapter not installed"};
    std::atomic_flag pumping_ = ATOMIC_FLAG_INIT;
};
} // namespace toi
