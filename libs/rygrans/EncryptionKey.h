#pragma once
#include <vector>
#include <cstdint>
#include "Config.h"

// Binary encryption key.
//
// The key can be generated from a 32-bit seed (Mersenne Twister) or
// given directly as a bit string. Both sides must use the same key.
// The key is read bit by bit and wraps around when the end is reached.
//
// Note: deriving the key from a 32-bit seed is a demo convenience.
// The effective key space is then only 2^32, which is not secure.
// For real use, pass a long random key directly with --key.
struct EncryptionKey {
    std::vector<uint8_t> bits;
    size_t   index = 0;
    uint32_t seed  = 0;

    // Generate a deterministic key of key_length bits from a seed.
    void init_from_seed(uint32_t s, size_t key_length = KEY_LENGTH);

    // Use the given bits directly as the key (seed stays 0).
    void init_from_bits(const std::vector<uint8_t>& key_bits);

    // Return the next key bit and advance (circular).
    // With no key at all, always return true (model updates every step).
    bool get_next_bit();

    bool empty() const { return bits.empty(); }
};
