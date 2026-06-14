#include "Compressor.h"

#include <iostream>
#include <fstream>
#include <vector>
#include <cstring>

#include "platform.h"
#include "rans_byte.h"
#include "Config.h"
#include "Snapshot.h"
#include "AdaptiveModel.h"
#include "EncryptionKey.h"

using namespace std;
extern uint32_t REBUILD_INTERVAL;

static vector<uint8_t> compress_block(const uint8_t* data, size_t N,
                                       EncryptionKey& enc_key) {
    enc_key.index = 0;

    size_t num_intervals = (N + REBUILD_INTERVAL - 1) / REBUILD_INTERVAL;

    vector<ModelSnapshot> snaps(num_intervals);
    AdaptiveModel model;
    model.init();

    for (size_t i = 0; i < N; i++) {
        if (i % REBUILD_INTERVAL == 0) {
            size_t idx = i / REBUILD_INTERVAL;
            memcpy(snaps[idx].freqs, model.freqs, sizeof(model.freqs));
            snaps[idx].total     = model.total;
            snaps[idx].key_index = enc_key.index;
        }
        if (enc_key.get_next_bit())
            model.update(data[i]);
    }

    vector<vector<RansEncSymbol>> tables(num_intervals,
                                         vector<RansEncSymbol>(256));
    for (size_t idx = 0; idx < num_intervals; idx++) {
        AdaptiveModel m;
        memcpy(m.freqs, snaps[idx].freqs, sizeof(m.freqs));
        m.total = snaps[idx].total;
        m.buildEncTable(tables[idx].data());
    }

    RansState rans;
    RansEncInit(&rans);
    vector<uint8_t> out_buf(N * 2 + 1024);
    uint8_t* ptr = out_buf.data() + out_buf.size();

    for (size_t i = N; i > 0; i--) {
        size_t pos      = i - 1;
        size_t interval = pos / REBUILD_INTERVAL;
        RansEncPutSymbol(&rans, &ptr, &tables[interval][data[pos]]);
    }

    RansEncFlush(&rans, &ptr);

    size_t comp_size = (out_buf.data() + out_buf.size()) - ptr;
    return vector<uint8_t>(ptr, ptr + comp_size);
}

// File format:
//   [uint32] seed          (0 if key was provided directly via --key)
//   [uint32] total_original_size
//   for each block:
//     [uint32] original_block_size
//     [uint32] compressed_block_size
//     [bytes]  compressed_block_data
void compress(const string& input_path, const string& output_path,
              EncryptionKey& enc_key) {
    ifstream in(input_path, ios::binary);
    if (!in) { cerr << "Error opening input file\n"; return; }

    ofstream out(output_path, ios::binary);
    if (!out) { cerr << "Error creating output file\n"; return; }

    in.seekg(0, ios::end);
    uint32_t total_orig = (uint32_t)in.tellg();
    in.seekg(0, ios::beg);

    // Write seed (0 means key was injected directly — decompressor must
    // also receive the key directly in that case)
    out.write((char*)&enc_key.seed, sizeof(enc_key.seed));
    out.write((char*)&total_orig,   sizeof(total_orig));

    vector<uint8_t> buffer(BLOCK_SIZE);
    size_t total_comp = sizeof(enc_key.seed) + sizeof(total_orig);

    while (in) {
        in.read((char*)buffer.data(), BLOCK_SIZE);
        size_t bytes_read = in.gcount();
        if (bytes_read == 0) break;

        vector<uint8_t> comp = compress_block(buffer.data(), bytes_read, enc_key);

        uint32_t ob = (uint32_t)bytes_read;
        uint32_t cb = (uint32_t)comp.size();
        out.write((char*)&ob, sizeof(ob));
        out.write((char*)&cb, sizeof(cb));
        out.write((char*)comp.data(), comp.size());
        total_comp += sizeof(ob) + sizeof(cb) + comp.size();
    }

    cout << "Compressed: " << total_orig << " -> " << total_comp << " bytes\n";
}