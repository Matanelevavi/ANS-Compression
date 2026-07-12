#pragma once
#include <cstdint>

#include "rans_byte.h"
#include "Config.h"
#include "Snapshot.h"

// Order-0 adaptive probability model over a 256-symbol alphabet.
//
// The model keeps a frequency counter per symbol, plus a permutation
// that gives the current order of the symbols in the interval
// partition. Swapping neighbors in this order is the "selective swap"
// idea from Section 3.4 of the paper: it hides the partition layout
// from an attacker at almost no cost.
struct AdaptiveModel {
    uint32_t freqs[256];   // symbol frequencies
    uint32_t total;        // sum of all frequencies
    uint8_t  perm[256];    // perm[pos] = symbol placed at position pos
    uint8_t  pos_of[256];  // pos_of[sym] = current position of symbol

    // Start with frequency 1 for every symbol (Laplace smoothing)
    // and the identity order. This avoids zero probabilities.
    void init();

    // Increment the frequency of sym; halve everything on overflow.
    void update(uint8_t sym);

    // Swap sym with its right neighbor in the current order
    // (paper, Section 3.4). Wraps around at the end.
    void swap_step(uint8_t sym);

    // Save / restore the full model state.
    void save(ModelSnapshot& snap) const;
    void load(const ModelSnapshot& snap);

    // Build the rANS encoder table for the current state.
    // esyms is indexed by symbol value.
    void buildEncTable(RansEncSymbol esyms[256]) const;

    // Build the rANS decoder table and the slot-to-symbol lookup.
    void buildDecTable(RansDecSymbol dsyms[256],
                       uint8_t slot_to_symbol[PROB_SCALE]) const;
};
