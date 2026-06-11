#include "AdaptiveModel.h"

void AdaptiveModel::init() {
    for (int i = 0; i < 256; i++) freqs[i] = 1;
    total = 256;
}

void AdaptiveModel::update(uint8_t sym) {
    freqs[sym]++;
    total++;
    // Halve all frequencies when total grows too large (prevents overflow)
    // +1 before shifting ensures no symbol drops to zero
    if (total >= (1u << 27)) {
        total = 0;
        for (int i = 0; i < 256; i++) {
            freqs[i] = (freqs[i] + 1) >> 1;
            total += freqs[i];
        }
    }
}

// Helper: normalize raw frequencies to sum exactly to PROB_SCALE
static void normalize(const uint32_t freqs[256], uint32_t norm[256]) {
    uint32_t total = 0;
    for (int i = 0; i < 256; i++) total += freqs[i];

    uint32_t sum = 0;
    for (int i = 0; i < 256; i++) {
        uint32_t p = (uint32_t)(((uint64_t)freqs[i] * PROB_SCALE) / total);
        norm[i] = (p == 0) ? 1 : p;
        sum += norm[i];
    }

    // Fix rounding overshoot: subtract from largest symbols
    while (sum > PROB_SCALE) {
        int best = -1; uint32_t bv = 0;
        for (int i = 0; i < 256; i++)
            if (norm[i] > 1 && norm[i] > bv) { bv = norm[i]; best = i; }
        if (best == -1) break;
        norm[best]--; sum--;
    }

    // Fix rounding undershoot: add to largest symbol
    while (sum < PROB_SCALE) {
        int best = -1; uint32_t bv = 0;
        for (int i = 0; i < 256; i++)
            if (norm[i] > bv) { bv = norm[i]; best = i; }
        if (best == -1) break;
        norm[best]++; sum++;
    }
}

void AdaptiveModel::buildEncTable(RansEncSymbol esyms[256]) const {
    uint32_t norm[256];
    normalize(freqs, norm);

    uint32_t start = 0;
    for (int i = 0; i < 256; i++) {
        RansEncSymbolInit(&esyms[i], start, norm[i], PROB_BITS);
        start += norm[i];
    }
}

void AdaptiveModel::buildDecTable(RansDecSymbol dsyms[256],
                                   uint8_t slot_to_symbol[PROB_SCALE]) const {
    uint32_t norm[256];
    normalize(freqs, norm);

    uint32_t start = 0;
    for (int i = 0; i < 256; i++) {
        RansDecSymbolInit(&dsyms[i], start, norm[i]);
        for (uint32_t j = 0; j < norm[i]; j++)
            slot_to_symbol[start + j] = (uint8_t)i;
        start += norm[i];
    }
}
