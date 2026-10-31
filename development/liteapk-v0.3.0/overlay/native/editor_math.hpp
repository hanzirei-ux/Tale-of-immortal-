#pragma once
#include <cmath>
#include <cstdint>
#include <string>
namespace toi {
enum class AmountMode:int {Read=-1,Set=0,Add=1,Subtract=2};
struct AmountPlan {int64_t before{},target{},delta{};};
inline bool planAmount(int64_t current,int op,double input,int64_t maximum,AmountPlan& out,std::string& error){
    if(current<0){error="Current balance is negative; no edit attempted";return false;}
    if(maximum<0||maximum>1000000000000LL||!std::isfinite(input)||std::trunc(input)!=input||input<0||input>static_cast<double>(maximum)){
        error="Amount must be a non-negative whole number within this resource's limit";return false;
    }
    auto operand=static_cast<int64_t>(input);int64_t target{};
    switch(static_cast<AmountMode>(op)){
    case AmountMode::Set:target=operand;break;
    case AmountMode::Add:if(current>maximum-operand){error="Balance limit/overflow guard rejected addition";return false;}target=current+operand;break;
    case AmountMode::Subtract:if(operand>current){error="Cannot subtract more than the current amount";return false;}target=current-operand;break;
    default:error="Unsupported edit operation";return false;
    }
    if(target>maximum){error="Result exceeds the resource edit limit";return false;}
    out={current,target,target-current};return true;
}
inline bool planCapacity(int64_t before,int used,int factor,int oldBonus,int op,double input,AmountPlan& out,int& nextBonus,std::string& error){
    if(!planAmount(before,op,input,2000,out,error))return false;
    if(used<0||used>200000||out.target<used){error="Capacity cannot be lower than occupied item slots";return false;}
    if(out.target<1){error="At least one inventory slot must remain";return false;}
    if(factor!=1&&factor!=2){error="Unrecognized game capacity formula; no edit attempted";return false;}
    if(out.delta%factor){error="The existing game bag plugin requires changes in multiples of two";return false;}
    auto bonus=int64_t(oldBonus)+out.delta/factor;
    if(bonus< -2000||bonus>2000){error="Capacity bonus exceeds this build's limit";return false;}
    nextBonus=int(bonus);return true;
}
}
