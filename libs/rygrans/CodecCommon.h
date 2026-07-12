#pragma once
#include <fstream>
#include <cstdint>

#include "Config.h"
#include "AdaptiveModel.h"
#include "EncryptionKey.h"
#include "PrimingText.h"

// Helpers shared by the compressor and the decompressor.
// Both sides MUST perform exactly the same model transitions and
// consume key bits in exactly the same order, otherwise they diverge.

// Key-gated model transition for one processed symbol:
//   bit 1 decides whether the frequency of the symbol is updated,
//   bit 2 (only when swaps are enabled) decides whether the symbol
//         is swapped with its neighbor in the partition order.
inline void gated_step(AdaptiveModel& model, EncryptionKey& key,
                       uint8_t sym, bool swaps) {
    if (key.get_next_bit())
        model.update(sym);
    if (swaps && key.get_next_bit())
        model.swap_step(sym);
}

// Warm up the model on a public, well-known text before the real
// data (paper, Section 3.2). The updates are gated by the secret
// key, so the resulting model state is secret.
inline void prime_model(AdaptiveModel& model, EncryptionKey& key,
                        bool swaps) {
    for (size_t i = 0; i < PRIMING_TEXT_LENGTH; i++)
        gated_step(model, key, (uint8_t)PRIMING_TEXT[i], swaps);
}

// ---------------------------------------------------------------
// Compressed file header (all fields little-endian):
//   [u32] magic "ARNS"
//   [u8 ] format version
//   [u8 ] flags (seed stored / priming / swaps)
//   [u32] rebuild interval
//   [u32] key seed (0 when not stored)
//   [u64] original file size
// Followed by blocks:
//   [u32] original block size
//   [u32] compressed block size
//   [bytes] compressed block data
// ---------------------------------------------------------------

struct FileHeader {
    uint8_t  flags            = 0;
    uint32_t rebuild_interval = DEFAULT_REBUILD_INTERVAL;
    uint32_t seed             = 0;
    uint64_t original_size    = 0;
};

inline void write_header(std::ofstream& out, const FileHeader& h) {
    uint32_t magic   = FILE_MAGIC;
    uint8_t  version = FILE_VERSION;
    out.write((const char*)&magic,              sizeof(magic));
    out.write((const char*)&version,            sizeof(version));
    out.write((const char*)&h.flags,            sizeof(h.flags));
    out.write((const char*)&h.rebuild_interval, sizeof(h.rebuild_interval));
    out.write((const char*)&h.seed,             sizeof(h.seed));
    out.write((const char*)&h.original_size,    sizeof(h.original_size));
}

// Read and validate the header. Returns false on any problem.
inline bool read_header(std::ifstream& in, FileHeader& h) {
    uint32_t magic = 0;
    uint8_t  version = 0;
    if (!in.read((char*)&magic, sizeof(magic)))     return false;
    if (magic != FILE_MAGIC)                        return false;
    if (!in.read((char*)&version, sizeof(version))) return false;
    if (version != FILE_VERSION)                    return false;
    if (!in.read((char*)&h.flags, sizeof(h.flags)))                       return false;
    if (!in.read((char*)&h.rebuild_interval, sizeof(h.rebuild_interval))) return false;
    if (h.rebuild_interval == 0)                    return false;
    if (!in.read((char*)&h.seed, sizeof(h.seed)))                         return false;
    if (!in.read((char*)&h.original_size, sizeof(h.original_size)))       return false;
    return true;
}

// Header size in bytes (the fields above, written without padding).
static const size_t HEADER_SIZE = 4 + 1 + 1 + 4 + 4 + 8;
