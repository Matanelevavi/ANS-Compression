#pragma once
#include <vector>
#include <cstdint>

// Binary encryption key.
// Generated deterministically from a seed using Mersenne Twister.
// Both encoder and decoder must use the same seed to produce the same key.
// The key is traversed circularly — when the end is reached, it wraps around.
struct EncryptionKey {
    std::vector<uint8_t> bits;
    size_t index;

    // Generate a deterministic random key from seed
    void init_from_seed(uint32_t seed, size_t key_length = 1000);

    // Manual initialization (for testing)
    void init(const std::vector<uint8_t>& key_bits);

    // Returns the next bit (circular).
    bool get_next_bit();
};
