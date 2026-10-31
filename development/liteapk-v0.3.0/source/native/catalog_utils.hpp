#pragma once
#include <algorithm>
#include <cctype>
#include <string>
namespace toi {
struct CatalogQuery {int type=-1,offset=0;std::string term;};
inline bool parseCatalogQuery(const std::string& raw,CatalogQuery& out){
    if(raw.size()>128||raw.empty()||raw.front()!='@')return false;
    auto first=raw.find('|'),last=raw.rfind('|');
    if(first==std::string::npos||last==first||std::count(raw.begin(),raw.end(),'|')!=2)return false;
    auto t=raw.substr(1,first-1),page=raw.substr(last+1);
    auto numeric=[](const std::string& v){if(v.empty())return false;size_t start=v[0]=='-'?1:0;return start<v.size()&&std::all_of(v.begin()+static_cast<std::string::difference_type>(start),v.end(),[](char c){return c>='0'&&c<='9';});};
    if(!numeric(t)||!numeric(page)||page[0]=='-')return false;
    try{out.type=std::stoi(t);out.offset=std::stoi(page);}catch(...){return false;}
    if(out.type< -1||out.type>255||out.offset<0||out.offset>100000)return false;
    out.term=raw.substr(first+1,last-first-1);return out.term.size()<=80;
}
inline std::string foldAscii(std::string s){for(char& c:s)if(static_cast<unsigned char>(c)<128)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));return s;}
inline int matchRank(const std::string& name,const std::string& id,const std::string& term){auto n=foldAscii(name),k=foldAscii(term);if(k.empty())return 0;if(n.rfind(k,0)==0||id.rfind(k,0)==0)return 0;return n.find(k)!=std::string::npos||id.find(k)!=std::string::npos?1:-1;}
inline std::string safeCatalogName(std::string s){for(char& c:s)if(c=='\n'||c=='\r'||c=='\t')c=' ';return s;}
}
