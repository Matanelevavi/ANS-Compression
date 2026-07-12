#include "EncryptionKey.h"
#include <random>

void EncryptionKey::init_from_seed(uint32_t s, size_t key_length) {
    seed = s;
    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> dist(0, 1);
    bits.resize(key_length);
    for (size_t i = 0; i < key_length; i++)
        bits[i] = (uint8_t)dist(rng);
    index = 0;
}

void EncryptionKey::init_from_bits(const std::vector<uint8_t>& key_bits) {
    seed  = 0;
    bits  = key_bits;
    index = 0;
}

bool EncryptionKey::get_next_bit() {
    if (bits.empty()) return true;  // no key: the model updates at every step
    bool bit = (bits[index] != 0);
    index = (index + 1) % bits.size();
    return bit;
}
