#include "sha256.hpp"
#include <algorithm>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <sstream>
namespace toi {
namespace {
constexpr uint32_t k[64] = {
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
uint32_t rr(uint32_t x, int n) { return (x >> n) | (x << (32-n)); }
}
void Sha256::compress(const uint8_t* b) {
    uint32_t w[64]{};
    for (int i=0; i<16; ++i) w[i] = uint32_t(b[4*i])<<24 | uint32_t(b[4*i+1])<<16 |
                                    uint32_t(b[4*i+2])<<8 | b[4*i+3];
    for (int i=16; i<64; ++i) {
        auto s0=rr(w[i-15],7)^rr(w[i-15],18)^(w[i-15]>>3);
        auto s1=rr(w[i-2],17)^rr(w[i-2],19)^(w[i-2]>>10);
        w[i]=w[i-16]+s0+w[i-7]+s1;
    }
    auto a=h_[0],b0=h_[1],c=h_[2],d=h_[3],e=h_[4],f=h_[5],g=h_[6],h=h_[7];
    for (int i=0;i<64;++i) {
        auto t1=h+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+k[i]+w[i];
        auto t2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&b0)^(a&c)^(b0&c));
        h=g;g=f;f=e;e=d+t1;d=c;c=b0;b0=a;a=t1+t2;
    }
    h_[0]+=a;h_[1]+=b0;h_[2]+=c;h_[3]+=d;h_[4]+=e;h_[5]+=f;h_[6]+=g;h_[7]+=h;
}
void Sha256::update(const void* input, size_t bytes) {
    auto p=static_cast<const uint8_t*>(input);
    bytes_+=bytes;
    while (bytes) {
        auto n=std::min(bytes,64-used_);
        std::memcpy(block_.data()+used_,p,n);
        used_+=n;p+=n;bytes-=n;
        if (used_==64) { compress(block_.data()); used_=0; }
    }
}
std::string Sha256::finish() {
    const auto bits=bytes_*8;
    block_[used_++]=0x80;
    if (used_>56) { std::fill(block_.begin()+used_,block_.end(),0);compress(block_.data());used_=0; }
    std::fill(block_.begin()+used_,block_.begin()+56,0);
    for (int i=0;i<8;++i) block_[63-i]=uint8_t(bits>>(8*i));
    compress(block_.data());
    std::ostringstream out;
    out<<std::hex<<std::setfill('0');
    for (auto x:h_) out<<std::setw(8)<<x;
    return out.str();
}
bool hashFile(const std::string& path, std::string& hash, std::string& error) {
    std::ifstream file(path,std::ios::binary);
    if (!file) { error="Cannot read baseline file"; return false; }
    Sha256 s;std::array<char,65536> b{};
    while (file.read(b.data(), b.size()) || file.gcount()) s.update(b.data(),size_t(file.gcount()));
    if (!file.eof()) { error="I/O error while hashing baseline";return false; }
    hash=s.finish();return true;
}
} // namespace toi
