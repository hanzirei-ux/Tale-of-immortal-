#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <array>
namespace toi {
class Sha256 {
public:
    void update(const void* input, size_t bytes);
    std::string finish();
private:
    void compress(const uint8_t* block);
    std::array<uint32_t, 8> h_{{0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                              0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}};
    std::array<uint8_t, 64> block_{};
    uint64_t bytes_{0};
    size_t used_{0};
};
bool hashFile(const std::string& path, std::string& hash, std::string& error);
} // namespace toi
