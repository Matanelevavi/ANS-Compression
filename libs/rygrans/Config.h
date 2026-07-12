#pragma once
#include <cstdint>

// rANS probability scale: all frequency tables are normalized to this sum.
#define PROB_BITS  14
#define PROB_SCALE (1u << PROB_BITS)  // 16384

// The input file is processed in blocks of this size (1 MB).
#define BLOCK_SIZE (1024 * 1024)

// Default number of symbols between probability table rebuilds.
#define DEFAULT_REBUILD_INTERVAL 512

// Number of key bits generated from a seed.
#define KEY_LENGTH 1000

// Compressed file format identification.
#define FILE_MAGIC   0x534E5241u  // the bytes "ARNS" in little-endian order
#define FILE_VERSION 2

// Header flag bits.
#define FLAG_SEED_STORED 0x01  // the key seed is stored in the header
#define FLAG_PRIMING     0x02  // the model was primed with a known text
#define FLAG_SWAPS       0x04  // selective alphabet swaps are enabled

// Options chosen at compression time.
// They are written into the file header, so the decompressor
// always uses the same settings as the compressor.
struct CodecParams {
    uint32_t rebuild_interval = DEFAULT_REBUILD_INTERVAL;
    bool priming    = true;   // warm up the model with a known text (paper, Section 3.2)
    bool swaps      = true;   // selective alphabet swaps (paper, Section 3.4)
    bool store_seed = true;   // write the seed into the header (demo convenience)
};
