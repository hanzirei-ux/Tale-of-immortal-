#pragma once
#include <cmath>
#include <iomanip>
#include <sstream>
#include <string>
namespace toi {
inline std::string jsonString(const std::string& value){
    std::ostringstream s;s<<'"';constexpr char hex[]="0123456789abcdef";
    for(unsigned char c:value){if(c=='"'||c=='\\')s<<'\\'<<char(c);else if(c<32)s<<"\\u00"<<hex[c>>4]<<hex[c&15];else s<<char(c);}s<<'"';return s.str();
}
inline std::string jsonNumber(double value){if(!std::isfinite(value))return "null";std::ostringstream s;s<<std::setprecision(17)<<value;return s.str();}
inline const char* jsonBool(bool value){return value?"true":"false";}
}
