#pragma once
#include <cstdint>

#include "rans_byte.h"
#include "Config.h"

// Order-0 adaptive probability model over a 256-symbol alphabet.
// Frequencies are updated symbol by symbol and used to build rANS tables.
struct AdaptiveModel {
    uint32_t freqs[256];
    uint32_t total;

    // Initialize with Laplace smoothing (freq=1 per symbol)
    // Guarantees no symbol has zero probability before any data is seen
    void init();

    // Increment frequency of sym; halve all frequencies on overflow
    void update(uint8_t sym);

    // Build rANS encoder table from current model state
    void buildEncTable(RansEncSymbol esyms[256]) const;

    // Build rANS decoder table + slot-to-symbol lookup from current model state
    void buildDecTable(RansDecSymbol dsyms[256],
                       uint8_t slot_to_symbol[PROB_SCALE]) const;
};
