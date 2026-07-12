#pragma once
#include <cstdint>

// A snapshot of the full adaptive model state, taken at the start of
// each rebuild interval during the forward pass of the encoder.
// The backward pass (pass 2) uses it to rebuild the exact probability
// table that was active when each symbol was encoded.
struct ModelSnapshot {
    uint32_t freqs[256];  // symbol frequencies
    uint32_t total;       // sum of all frequencies
    uint8_t  perm[256];   // current order of the symbols in the partition
};
