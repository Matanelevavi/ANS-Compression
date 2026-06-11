#pragma once
#include <cstdint>

// Snapshot of the adaptive model state at the start of each interval.
// Used by the encoder (pass 2) to reconstruct the exact model state
// that was active when each symbol was encoded.
struct ModelSnapshot {
    uint32_t freqs[256];
    uint32_t total;
    size_t   key_index;
};
