#pragma once
#include "bridge.hpp"
#include "modifiers.hpp"
#include "control_gateway.hpp"
#include "request_mailbox.hpp"
namespace toi {
PolicyStore& runtimePolicyStore();
ControlReadiness runtimeControlReadiness();
ControlReply runtimeApplyControl(int id,const std::string& key,bool enabled,double value);
std::string runtimeControlDiagnostics();
bool startGameRuntime(std::shared_ptr<Backend> backend,std::string& error);
std::string runtimeStatus();
uint64_t runtimeCapabilities();
int runtimeHookCount();
// Requests are executed only by the installed Unity scripting-thread callback.
uint64_t queueGameRequest(const std::string& kind,const std::string& key,int op,double value,std::string& error);
std::string gameRequestResult();
std::vector<GameReply> takeGameRequestResults();
void cancelGameRequests();
}
