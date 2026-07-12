#include "Decompressor.h"

#include <iostream>
#include <fstream>
#include <vector>

#include "rans_byte.h"
#include "AdaptiveModel.h"
#include "CodecCommon.h"

using namespace std;

bool decompress(const string& input_path, const string& output_path,
                EncryptionKey& enc_key) {
    ifstream in(input_path, ios::binary);
    if (!in) {
        cerr << "Error: cannot open compressed file: " << input_path << "\n";
        return false;
    }

    FileHeader header;
    if (!read_header(in, header)) {
        cerr << "Error: not a valid compressed file (bad header)\n";
        return false;
    }

    const bool priming = (header.flags & FLAG_PRIMING) != 0;
    const bool swaps   = (header.flags & FLAG_SWAPS)   != 0;
    const uint32_t R   = header.rebuild_interval;

    // Key priority:
    //   1. a key given on the command line (--seed or --key) is used as-is;
    //   2. otherwise, if the header stores a seed, rebuild the key from it;
    //   3. otherwise the file cannot be decrypted without a key.
    if (enc_key.empty()) {
        if (header.flags & FLAG_SEED_STORED) {
            enc_key.init_from_seed(header.seed);
        } else {
            cerr << "Error: this file does not store its key seed. "
                 << "Pass the key with --seed or --key.\n";
            return false;
        }
    }

    ofstream out(output_path, ios::binary);
    if (!out) {
        cerr << "Error: cannot create output file: " << output_path << "\n";
        return false;
    }

    // Replicate the encoder's model evolution exactly:
    // same init, same priming, same key bit consumption.
    AdaptiveModel model;
    model.init();
    if (priming)
        prime_model(model, enc_key, swaps);

    RansDecSymbol dsyms[256];
    uint8_t slot_to_sym[PROB_SCALE];

    uint64_t total_written = 0;

    while (in.peek() != EOF) {
        uint32_t orig_b = 0, comp_b = 0;
        if (!in.read((char*)&orig_b, sizeof(orig_b))) break;
        if (!in.read((char*)&comp_b, sizeof(comp_b))) break;

        // Basic sanity limits guard against corrupted headers.
        if (orig_b > BLOCK_SIZE || comp_b < 4 ||
            comp_b > 2 * BLOCK_SIZE + 1024) {
            cerr << "Error: corrupted file (bad block sizes)\n";
            return false;
        }

        // With a wrong key the rANS state goes out of sync and may
        // try to read more bytes than the block really has. We pad
        // the buffer so those reads stay inside it. The padding byte
        // is 0xFF, not 0x00: the rANS renormalization loop reads
        // bytes until the state reaches 2^23, and a run of 0x00 bytes
        // would never raise it (0<<8 | 0 == 0), looping off the end.
        // 0xFF guarantees the loop stops within a few reads, so each
        // symbol consumes at most 4 bytes.
        size_t safe_size = 8 + (size_t)orig_b * 4;
        if (safe_size < comp_b) safe_size = comp_b;
        vector<uint8_t> comp_data(safe_size, 0xFF);
        if (!in.read((char*)comp_data.data(), comp_b)) {
            cerr << "Error: corrupted file (truncated block)\n";
            return false;
        }

        uint8_t* ptr = comp_data.data();
        RansState rans;
        RansDecInit(&rans, &ptr);

        // Tables are rebuilt at interval boundaries, matching the
        // snapshots the encoder took at the same positions.
        model.buildDecTable(dsyms, slot_to_sym);
        uint32_t next_rebuild = R;

        vector<uint8_t> output;
        output.reserve(orig_b);

        for (uint32_t i = 0; i < orig_b; i++) {
            if (i == next_rebuild) {
                model.buildDecTable(dsyms, slot_to_sym);
                next_rebuild += R;
            }

            uint32_t cum = RansDecGet(&rans, PROB_BITS);
            uint8_t  sym = slot_to_sym[cum];
            output.push_back(sym);

            RansDecAdvanceSymbol(&rans, &ptr, &dsyms[sym], PROB_BITS);

            gated_step(model, enc_key, sym, swaps);
        }

        out.write((char*)output.data(), output.size());
        total_written += output.size();
    }

    if (!out) {
        cerr << "Error: failed writing output file (disk full?)\n";
        return false;
    }

    if (total_written != header.original_size) {
        cerr << "Warning: decompressed size (" << total_written
             << ") does not match the size in the header ("
             << header.original_size << ")\n";
    }

    cout << "Decompressed to: " << output_path << "\n";
    return true;
}
