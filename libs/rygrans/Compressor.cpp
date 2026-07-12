#include "Compressor.h"

#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>

#include "rans_byte.h"
#include "Snapshot.h"
#include "AdaptiveModel.h"
#include "CodecCommon.h"

using namespace std;

// Compress one block of N bytes.
//
// Pass 1 (forward): walk over the data, apply the key-gated model
// transitions, and save a snapshot of the model at the start of
// every rebuild interval.
//
// Pass 2 (backward): rANS encodes last-symbol-first, so we walk the
// intervals in reverse. For each interval we rebuild its encoder
// table from the snapshot (one table at a time, so memory stays
// small) and encode the interval's symbols in reverse order.
//
// The model and the key are shared across blocks: they carry their
// state from one block to the next, exactly like the decoder does.
static vector<uint8_t> compress_block(const uint8_t* data, size_t N,
                                      AdaptiveModel& model,
                                      EncryptionKey& enc_key,
                                      const CodecParams& params) {
    const size_t R = params.rebuild_interval;
    const size_t num_intervals = (N + R - 1) / R;

    // Pass 1: forward scan with snapshots.
    vector<ModelSnapshot> snaps(num_intervals);
    for (size_t i = 0; i < N; i++) {
        if (i % R == 0)
            model.save(snaps[i / R]);
        gated_step(model, enc_key, data[i], params.swaps);
    }

    // Pass 2: backward rANS encoding, one interval table at a time.
    RansState rans;
    RansEncInit(&rans);
    vector<uint8_t> out_buf(N * 2 + 1024);
    uint8_t* ptr = out_buf.data() + out_buf.size();

    AdaptiveModel snap_model;
    RansEncSymbol esyms[256];
    for (size_t idx = num_intervals; idx > 0; idx--) {
        const size_t interval = idx - 1;
        snap_model.load(snaps[interval]);
        snap_model.buildEncTable(esyms);

        const size_t lo = interval * R;
        const size_t hi = min(N, lo + R);
        for (size_t i = hi; i > lo; i--)
            RansEncPutSymbol(&rans, &ptr, &esyms[data[i - 1]]);
    }

    RansEncFlush(&rans, &ptr);

    const size_t comp_size = (out_buf.data() + out_buf.size()) - ptr;
    return vector<uint8_t>(ptr, ptr + comp_size);
}

bool compress(const string& input_path, const string& output_path,
              EncryptionKey& enc_key, const CodecParams& params) {
    ifstream in(input_path, ios::binary);
    if (!in) {
        cerr << "Error: cannot open input file: " << input_path << "\n";
        return false;
    }

    ofstream out(output_path, ios::binary);
    if (!out) {
        cerr << "Error: cannot create output file: " << output_path << "\n";
        return false;
    }

    in.seekg(0, ios::end);
    uint64_t total_orig = (uint64_t)in.tellg();
    in.seekg(0, ios::beg);

    FileHeader header;
    header.rebuild_interval = params.rebuild_interval;
    header.original_size    = total_orig;
    if (params.priming) header.flags |= FLAG_PRIMING;
    if (params.swaps)   header.flags |= FLAG_SWAPS;
    if (params.store_seed && enc_key.seed != 0) {
        header.flags |= FLAG_SEED_STORED;
        header.seed = enc_key.seed;
    }
    write_header(out, header);

    // The model and key state run continuously over the whole file.
    AdaptiveModel model;
    model.init();
    if (params.priming)
        prime_model(model, enc_key, params.swaps);

    vector<uint8_t> buffer(BLOCK_SIZE);
    uint64_t total_comp = HEADER_SIZE;

    while (in) {
        in.read((char*)buffer.data(), BLOCK_SIZE);
        size_t bytes_read = (size_t)in.gcount();
        if (bytes_read == 0) break;

        vector<uint8_t> comp = compress_block(buffer.data(), bytes_read,
                                              model, enc_key, params);

        uint32_t ob = (uint32_t)bytes_read;
        uint32_t cb = (uint32_t)comp.size();
        out.write((char*)&ob, sizeof(ob));
        out.write((char*)&cb, sizeof(cb));
        out.write((char*)comp.data(), comp.size());
        total_comp += sizeof(ob) + sizeof(cb) + comp.size();
    }

    if (!out) {
        cerr << "Error: failed writing output file (disk full?)\n";
        return false;
    }

    cout << "Compressed: " << total_orig << " -> " << total_comp << " bytes\n";
    return true;
}
