// Command line tool for the adaptive rANS compressor with
// integrated encryption (key-gated model updates).
//
// Based on the scheme of Klein & Shapira,
// "Integrated Encryption in Dynamic Arithmetic Compression",
// applied here to rANS instead of arithmetic coding.

#include <iostream>
#include <string>
#include <vector>
#include <cstdint>
#include <random>
#include <stdexcept>

#include "Config.h"
#include "Compressor.h"
#include "Decompressor.h"
#include "EncryptionKey.h"

using namespace std;

static void print_usage() {
    cout <<
        "Usage:\n"
        "  compressor c <input> <output> [options]   compress\n"
        "  compressor d <input> <output> [options]   decompress\n"
        "\n"
        "Key options (both modes):\n"
        "  --seed N        derive the key from a 32-bit seed\n"
        "  --key BITS      use BITS (a string of 0/1) directly as the key\n"
        "  --flip-bit N    flip key bit N (for sensitivity experiments)\n"
        "\n"
        "Compression options (stored in the file header):\n"
        "  --interval N    rebuild tables every N symbols (default "
        << DEFAULT_REBUILD_INTERVAL << ")\n"
        "  --no-prime      do not prime the model with the known text\n"
        "  --no-swaps      disable selective alphabet swaps\n"
        "  --no-store-seed do not store the key seed in the output file\n"
        "\n"
        "When compressing without --seed/--key, a random seed is chosen.\n"
        "By default that seed is stored in the file header, so the file\n"
        "decrypts itself with no key needed on the command line. That is a\n"
        "convenience for testing, NOT real secrecy: anyone with the file\n"
        "can decompress it. For an actual secret key, compress with\n"
        "--no-store-seed and share the key (--seed or --key) separately.\n";
}

// Parse a decimal string into uint32_t. Throws on bad input.
static uint32_t parse_u32(const string& text, const string& option) {
    try {
        size_t pos = 0;
        unsigned long v = stoul(text, &pos);
        if (pos != text.size() || v > 0xFFFFFFFFul)
            throw invalid_argument("range");
        return (uint32_t)v;
    } catch (...) {
        throw invalid_argument("invalid value for " + option + ": " + text);
    }
}

int main(int argc, char** argv) {
    if (argc < 4) {
        print_usage();
        return 1;
    }

    string mode   = argv[1];
    string input  = argv[2];
    string output = argv[3];

    if (mode != "c" && mode != "d") {
        cerr << "Error: unknown mode '" << mode << "' (use c or d)\n";
        return 1;
    }
    const bool compressing = (mode == "c");

    EncryptionKey enc_key;
    CodecParams params;
    long flip_bit_index = -1;

    try {
        for (int i = 4; i < argc; ++i) {
            string arg = argv[i];
            if (arg == "--seed" && i + 1 < argc) {
                enc_key.init_from_seed(parse_u32(argv[++i], "--seed"));
            }
            else if (arg == "--key" && i + 1 < argc) {
                vector<uint8_t> bits;
                for (char c : string(argv[++i])) {
                    if (c != '0' && c != '1')
                        throw invalid_argument("--key must contain only 0 and 1");
                    bits.push_back(c == '1' ? 1 : 0);
                }
                if (bits.empty())
                    throw invalid_argument("--key must not be empty");
                enc_key.init_from_bits(bits);
            }
            else if (arg == "--flip-bit" && i + 1 < argc) {
                flip_bit_index = (long)parse_u32(argv[++i], "--flip-bit");
            }
            else if (arg == "--interval" && i + 1 < argc) {
                if (!compressing)
                    throw invalid_argument(
                        "--interval is a compression option; "
                        "the decompressor reads it from the file header");
                params.rebuild_interval = parse_u32(argv[++i], "--interval");
                if (params.rebuild_interval == 0)
                    throw invalid_argument("--interval must be at least 1");
            }
            else if (arg == "--no-prime")      { params.priming = false; }
            else if (arg == "--no-swaps")      { params.swaps = false; }
            else if (arg == "--no-store-seed") { params.store_seed = false; }
            else {
                throw invalid_argument("unknown option: " + arg);
            }
        }
    } catch (const exception& e) {
        cerr << "Error: " << e.what() << "\n";
        return 1;
    }

    // Compressing without a key: choose a random seed.
    if (compressing && enc_key.empty()) {
        random_device rd;
        uint32_t seed = rd();
        if (seed == 0) seed = 1;  // seed 0 means "no seed stored"
        enc_key.init_from_seed(seed);
    }

    // Flip one key bit (used by the sensitivity experiments).
    if (flip_bit_index >= 0) {
        if (enc_key.empty()) {
            cerr << "Error: --flip-bit needs a key (--seed or --key)\n";
            return 1;
        }
        if (flip_bit_index >= (long)enc_key.bits.size()) {
            cerr << "Error: --flip-bit index " << flip_bit_index
                 << " is out of range (key has " << enc_key.bits.size()
                 << " bits)\n";
            return 1;
        }
        enc_key.bits[flip_bit_index] ^= 1;
    }

    bool ok = compressing
        ? compress(input, output, enc_key, params)
        : decompress(input, output, enc_key);

    return ok ? 0 : 1;
}
