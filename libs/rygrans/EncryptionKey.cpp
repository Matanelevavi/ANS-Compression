#include "EncryptionKey.h"
#include <random>
using namespace std;


void EncryptionKey::init_from_seed(uint32_t seed, size_t key_length) {
    mt19937 rng(seed);
    uniform_int_distribution<int> dist(0, 1);
    bits.resize(key_length);
    for (size_t i = 0; i < key_length; i++)
        bits[i] = (uint8_t)dist(rng);
    index = 0;
}

void EncryptionKey::init(const vector<uint8_t>& key_bits) {
    bits  = key_bits;
    index = 0;
}

bool EncryptionKey::get_next_bit() {
    bool bit = (bits[index] != 0);
    index = (index + 1) % bits.size();
    return bit;
}
