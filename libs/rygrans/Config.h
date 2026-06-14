#pragma once
#include <cstdint>

// rANS probability scale
#define PROB_BITS        14
#define PROB_SCALE       (1 << PROB_BITS)   // 16384

// Block size for file streaming (1MB)
#define BLOCK_SIZE       (1024 * 1024)

// How often to rebuild probability tables (every N symbols)
extern uint32_t REBUILD_INTERVAL;