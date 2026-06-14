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

void decompress(const string& input_path, const string& output_path,
                EncryptionKey& enc_key) {
    ifstream in(input_path, ios::binary);
    if (!in) { cerr << "Error opening compressed file\n"; return; }

    ofstream out(output_path, ios::binary);
    if (!out) { cerr << "Error creating decompressed file\n"; return; }

    // Read seed from file header
    uint32_t file_seed;
    if (!in.read((char*)&file_seed, sizeof(file_seed))) return;

    uint32_t total_orig;
    if (!in.read((char*)&total_orig, sizeof(total_orig))) return;

    // Key priority:
    //   1. enc_key injected from outside (--seed or --key) → use as-is
    //   2. enc_key empty + file has seed                   → rebuild from file seed
    //   3. enc_key empty + file seed is 0                  → no key (all bits = 1)
    if (enc_key.empty()) {
            if (file_seed != 0)
                enc_key.init_from_seed(file_seed);
        }

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

        AdaptiveModel model;
        model.init();
        enc_key.index = 0;   // reset key position for each block

        RansDecSymbol dsyms[256];
        uint8_t slot_to_sym[PROB_SCALE];

        model.buildDecTable(dsyms, slot_to_sym);
        uint32_t next_rebuild = REBUILD_INTERVAL;

        vector<uint8_t> output;
        output.reserve(orig_b);

        for (uint32_t i = 0; i < orig_b; i++) {
            if (i == next_rebuild) {
                model.buildDecTable(dsyms, slot_to_sym);
                next_rebuild += REBUILD_INTERVAL;
            }

            uint32_t cum = RansDecGet(&rans, PROB_BITS);
            uint8_t  sym = slot_to_sym[cum];
            output.push_back(sym);

            RansDecAdvanceSymbol(&rans, &ptr, &dsyms[sym], PROB_BITS);

            if (enc_key.get_next_bit())
                model.update(sym);
        }

        out.write((char*)output.data(), output.size());
    }

    cout << "Decompressed to: " << output_path << endl;
}