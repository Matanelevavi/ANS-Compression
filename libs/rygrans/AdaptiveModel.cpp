#include "AdaptiveModel.h"
#include <cstring>

void AdaptiveModel::init() {
    for (int i = 0; i < 256; i++) {
        freqs[i]  = 1;
        perm[i]   = (uint8_t)i;
        pos_of[i] = (uint8_t)i;
    }
    total = 256;
}

void AdaptiveModel::update(uint8_t sym) {
    freqs[sym]++;
    total++;
    // Halve all frequencies when the total grows too large.
    // The +1 before shifting keeps every frequency above zero.
    if (total >= (1u << 27)) {
        total = 0;
        for (int i = 0; i < 256; i++) {
            freqs[i] = (freqs[i] + 1) >> 1;
            total += freqs[i];
        }
    }
}

void AdaptiveModel::swap_step(uint8_t sym) {
    uint8_t p = pos_of[sym];
    uint8_t q = (uint8_t)((p + 1) & 0xFF);  // right neighbor, wraps at 255
    uint8_t other = perm[q];
    perm[p] = other;
    perm[q] = sym;
    pos_of[sym]   = q;
    pos_of[other] = p;
}

void AdaptiveModel::save(ModelSnapshot& snap) const {
    memcpy(snap.freqs, freqs, sizeof(freqs));
    memcpy(snap.perm,  perm,  sizeof(perm));
    snap.total = total;
}

void AdaptiveModel::load(const ModelSnapshot& snap) {
    memcpy(freqs, snap.freqs, sizeof(freqs));
    memcpy(perm,  snap.perm,  sizeof(perm));
    total = snap.total;
    for (int pos = 0; pos < 256; pos++)
        pos_of[perm[pos]] = (uint8_t)pos;
}

// Scale the raw frequencies so they sum exactly to PROB_SCALE.
// Every symbol keeps at least frequency 1.
static void normalize(const uint32_t freqs[256], uint32_t norm[256]) {
    uint32_t total = 0;
    for (int i = 0; i < 256; i++) total += freqs[i];

    uint32_t sum = 0;
    for (int i = 0; i < 256; i++) {
        uint32_t p = (uint32_t)(((uint64_t)freqs[i] * PROB_SCALE) / total);
        norm[i] = (p == 0) ? 1 : p;
        sum += norm[i];
    }

    // Rounding overshoot: take away from the largest symbols.
    while (sum > PROB_SCALE) {
        int best = -1; uint32_t bv = 0;
        for (int i = 0; i < 256; i++)
            if (norm[i] > 1 && norm[i] > bv) { bv = norm[i]; best = i; }
        if (best == -1) break;
        norm[best]--; sum--;
    }

    // Rounding undershoot: give to the largest symbol.
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

    // Ranges are laid out in the current permutation order,
    // so the partition layout depends on the (secret) swap history.
    uint32_t start = 0;
    for (int pos = 0; pos < 256; pos++) {
        uint8_t sym = perm[pos];
        RansEncSymbolInit(&esyms[sym], start, norm[sym], PROB_BITS);
        start += norm[sym];
    }
}

void AdaptiveModel::buildDecTable(RansDecSymbol dsyms[256],
                                  uint8_t slot_to_symbol[PROB_SCALE]) const {
    uint32_t norm[256];
    normalize(freqs, norm);

    uint32_t start = 0;
    for (int pos = 0; pos < 256; pos++) {
        uint8_t sym = perm[pos];
        RansDecSymbolInit(&dsyms[sym], start, norm[sym]);
        for (uint32_t j = 0; j < norm[sym]; j++)
            slot_to_symbol[start + j] = sym;
        start += norm[sym];
    }
}
