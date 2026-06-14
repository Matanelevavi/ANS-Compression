#define NOMINMAX
#include <iostream>
#include <string>
#include <vector>
#include <cstdint>
#include <random>

#include "Compressor.h"
#include "Decompressor.h"
#include "EncryptionKey.h"

using namespace std;
int flip_bit_index = -1;
uint32_t REBUILD_INTERVAL = 512;

int main(int argc, char** argv) {
    if (argc < 4) {
        cout << "Usage:\n"
             << "  compressor.exe c <input> <output> [--seed N] [--key BITS] [--flip-bit N] [--interval N]\n"
             << "  compressor.exe d <input> <output> [--seed N] [--key BITS] [--flip-bit N] [--interval N]\n";
        return 1;
    }

    string mode   = argv[1];
    string input  = argv[2];
    string output = argv[3];

    EncryptionKey enc_key;

    // 1. סריקה דינמית של כל הארגומנטים משורת הפקודה
    for (int i = 4; i < argc; ++i) {
        string arg = argv[i];
        if (arg == "--seed" && i + 1 < argc) {
            uint32_t seed = (uint32_t)stoul(argv[++i]);
            enc_key.init_from_seed(seed);
        } 
        else if (arg == "--key" && i + 1 < argc) {
            vector<uint8_t> bits;
            for (char c : string(argv[++i]))
                if (c == '0' || c == '1')
                    bits.push_back(c == '1' ? 1 : 0);
            enc_key.init_from_bits(bits);
        } 
        else if (arg == "--flip-bit" && i + 1 < argc) {
            flip_bit_index = std::stoi(argv[++i]);
        } 
        else if (arg == "--interval" && i + 1 < argc) {
            REBUILD_INTERVAL = (uint32_t)std::stoul(argv[++i]);
        }
    }

    // 2. הגרלת מפתח אקראי לדחיסה אם לא סופק
    if (mode == "c" && enc_key.empty()) {
        random_device rd;
        enc_key.init_from_seed(rd());
    }

    if (flip_bit_index >= 0 && flip_bit_index < (int)enc_key.bits.size()) {
            enc_key.bits[flip_bit_index] ^= 1; // היפוך ביט 100 הרשמי!
        }

    if      (mode == "c") compress  (input, output, enc_key);
    else if (mode == "d") decompress(input, output, enc_key);
    else    cerr << "Unknown mode '" << mode << "' (use c or d)\n";

    return 0;
}