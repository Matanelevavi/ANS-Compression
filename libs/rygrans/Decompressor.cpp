#include "Decompressor.h"

#include <iostream>
#include <fstream>
#include <vector>

#include "platform.h"
#include "rans_byte.h"
#include "Config.h"
#include "AdaptiveModel.h"
#include "EncryptionKey.h"

using namespace std;

// -----------------------------------------------------------------------
// decompress
// Mirrors the encoder exactly:
//   - Same model initialization (Laplace smoothing)
//   - Same key seed and traversal order
//   - Decoder table rebuilt at the same interval boundaries as the encoder
//   - Model updated after each symbol with the same key-bit condition
// -----------------------------------------------------------------------
void decompress(const string& input_path, const string& output_path) {
    ifstream in(input_path, ios::binary);
    if (!in) { cerr << "Error opening compressed file\n"; return; }

    ofstream out(output_path, ios::binary);
    if (!out) { cerr << "Error creating decompressed file\n"; return; }

    uint32_t seed;
    if (!in.read((char*)&seed, sizeof(seed))) return;
  
    uint32_t total_orig;
    if (!in.read((char*)&total_orig, sizeof(total_orig))) return;

    EncryptionKey enc_key;
    enc_key.init_from_seed(seed);

    while (in.peek() != EOF) {
        uint32_t orig_b, comp_b;
        if (!in.read((char*)&orig_b, sizeof(orig_b))) break;
        if (!in.read((char*)&comp_b, sizeof(comp_b))) break;

        vector<uint8_t> comp_data(comp_b);
        if (!in.read((char*)comp_data.data(), comp_b)) {
            cerr << "Corrupted file\n"; return;
        }

        uint8_t* ptr = comp_data.data();
        RansState rans;
        RansDecInit(&rans, &ptr);

        // Must match encoder initialization exactly
        AdaptiveModel model;
        model.init();
        enc_key.index = 0;

        RansDecSymbol dsyms[256];
        uint8_t slot_to_sym[PROB_SCALE];

        // Build initial table before first symbol
        model.buildDecTable(dsyms, slot_to_sym);
        uint32_t next_rebuild = REBUILD_INTERVAL;

        vector<uint8_t> output;
        output.reserve(orig_b);

        for (uint32_t i = 0; i < orig_b; i++) {
            // Rebuild at the same interval boundaries as the encoder
            if (i == next_rebuild) {
                model.buildDecTable(dsyms, slot_to_sym);
                next_rebuild += REBUILD_INTERVAL;
            }

            uint32_t cum = RansDecGet(&rans, PROB_BITS);
            uint8_t  sym = slot_to_sym[cum];
            output.push_back(sym);

            RansDecAdvanceSymbol(&rans, &ptr, &dsyms[sym], PROB_BITS);

            // Must match encoder update condition exactly
            if (enc_key.get_next_bit())
                model.update(sym);
        }

        out.write((char*)output.data(), output.size());
    }

    cout << "Decompressed to: " << output_path << endl;
}
