#include "sha256.hpp"
#include <iostream>
int main(int argc,char** argv) {
    if(argc!=2) return 2;
    std::string hash,error;
    if(!toi::hashFile(argv[1],hash,error)) {std::cerr<<error<<'\n';return 1;}
    std::cout<<hash<<'\n';
}
