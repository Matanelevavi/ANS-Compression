#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>
#include <cstring>
#include <random>  
#include "rans/platform.h"
#include "rans/rans_byte.h"
#include "common/Config.h"

using namespace std;

// --- Configuration Constants ---
#define PROB_BITS       14
#define PROB_SCALE      (1 << PROB_BITS)
#define BLOCK_SIZE      (1024 * 1024)
#define REBUILD_INTERVAL 512   // כל כמה סימנים לשמור snapshot ולבנות טבלה מחדש

// --- Key Management ---
struct EncryptionKey {
    vector<uint8_t> bits;
    size_t index;

     void init_from_seed(uint32_t seed, size_t key_length = 1000) {
        mt19937 rng(seed);              // Mersenne Twister — רנדום דטרמיניסטי
        uniform_int_distribution<int> dist(0, 1);
        bits.resize(key_length);
        for (size_t i = 0; i < key_length; i++)
            bits[i] = (uint8_t)dist(rng);
        index = 0;
    }

    void init(const vector<uint8_t>& key_bits) {
        bits = key_bits;
        index = 0;
    }

    bool get_next_bit(bool dummy_mode = false) {
        if (dummy_mode || bits.empty()) return true;
        bool bit = (bits[index] != 0);
        index = (index + 1) % bits.size();
        return bit;
    }
};

// --- Adaptive Model ---
struct AdaptiveModel {
    uint32_t freqs[256];
    uint32_t total;

    void init() {
        for (int i = 0; i < 256; i++) freqs[i] = 1;
        total = 256;
    }

    void update(uint8_t sym) {
        freqs[sym]++;
        total++;
        if (total >= (1u << 27)) {
            total = 0;
            for (int i = 0; i < 256; i++) {
                freqs[i] = (freqs[i] + 1) >> 1;
                total += freqs[i];
            }
        }
    }

    void buildEncTable(RansEncSymbol esyms[256]) const {
        uint32_t norm[256] = {};
        uint32_t sum = 0;
        for (int i = 0; i < 256; i++) {
            uint32_t p = (uint32_t)(((uint64_t)freqs[i] * PROB_SCALE) / total);
            norm[i] = (p == 0) ? 1 : p;
            sum += norm[i];
        }
        while (sum > PROB_SCALE) {
            int best = -1; uint32_t bv = 0;
            for (int i = 0; i < 256; i++)
                if (norm[i] > 1 && norm[i] > bv) { bv = norm[i]; best = i; }
            if (best == -1) break;
            norm[best]--; sum--;
        }
        while (sum < PROB_SCALE) {
            int best = -1; uint32_t bv = 0;
            for (int i = 0; i < 256; i++)
                if (norm[i] > bv) { bv = norm[i]; best = i; }
            if (best == -1) break;
            norm[best]++; sum++;
        }
        uint32_t start = 0;
        for (int i = 0; i < 256; i++) {
            RansEncSymbolInit(&esyms[i], start, norm[i], PROB_BITS);
            start += norm[i];
        }
    }

    void buildDecTable(RansDecSymbol dsyms[256], uint8_t slot_to_symbol[PROB_SCALE]) const {
        uint32_t norm[256] = {};
        uint32_t sum = 0;
        for (int i = 0; i < 256; i++) {
            uint32_t p = (uint32_t)(((uint64_t)freqs[i] * PROB_SCALE) / total);
            norm[i] = (p == 0) ? 1 : p;
            sum += norm[i];
        }
        while (sum > PROB_SCALE) {
            int best = -1; uint32_t bv = 0;
            for (int i = 0; i < 256; i++)
                if (norm[i] > 1 && norm[i] > bv) { bv = norm[i]; best = i; }
            if (best == -1) break;
            norm[best]--; sum--;
        }
        while (sum < PROB_SCALE) {
            int best = -1; uint32_t bv = 0;
            for (int i = 0; i < 256; i++)
                if (norm[i] > bv) { bv = norm[i]; best = i; }
            if (best == -1) break;
            norm[best]++; sum++;
        }
        uint32_t start = 0;
        for (int i = 0; i < 256; i++) {
            RansDecSymbolInit(&dsyms[i], start, norm[i]);
            for (uint32_t j = 0; j < norm[i]; j++)
                slot_to_symbol[start + j] = (uint8_t)i;
            start += norm[i];
        }
    }
};

struct ModelSnapshot {
    uint32_t freqs[256];
    uint32_t total;
    size_t   key_index;   // מצב ה-enc_key בתחילת ה-interval
};

// --- Compress block ---
vector<uint8_t> compress_block(const uint8_t* data, size_t N,
                                EncryptionKey& enc_key, bool dummy_mode) {
    enc_key.index = 0;

    size_t num_intervals = (N + REBUILD_INTERVAL - 1) / REBUILD_INTERVAL;

    // מעבר 1: snapshot רק בתחילת כל interval — זיכרון: num_intervals * 1KB
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
        if (enc_key.get_next_bit(dummy_mode))
            model.update(data[i]);
    }

    // מעבר 2: קידוד הפוך
    // לכל interval: שחזר snapshot, הרץ קדימה עד הסימן המדויק, בנה טבלה פעם אחת
    RansState rans;
    RansEncInit(&rans);
    vector<uint8_t> out_buf(N * 2 + 1024);
    uint8_t* ptr = out_buf.data() + out_buf.size();

    // טבלאות מוכנות לכל ה-intervals — נבנות פעם אחת כל REBUILD_INTERVAL סימנים
    // במקום N פעמים — N/512 פעמים בלבד
    vector<vector<RansEncSymbol>> interval_tables(num_intervals,
                                                  vector<RansEncSymbol>(256));

    // בנה את טבלאות כל ה-intervals מראש (מעבר קצר קדימה)
    for (size_t idx = 0; idx < num_intervals; idx++) {
        AdaptiveModel m;
        memcpy(m.freqs, snaps[idx].freqs, sizeof(m.freqs));
        m.total = snaps[idx].total;
        m.buildEncTable(interval_tables[idx].data());
    }

    // קידוד: כל סימן משתמש בטבלה של ה-interval שלו
    for (size_t i = N; i > 0; i--) {
        size_t pos      = i - 1;
        size_t interval = pos / REBUILD_INTERVAL;
        RansEncPutSymbol(&rans, &ptr, &interval_tables[interval][data[pos]]);
    }

    RansEncFlush(&rans, &ptr);

    size_t comp_size = (out_buf.data() + out_buf.size()) - ptr;
    return vector<uint8_t>(ptr, ptr + comp_size);
}

// --- Compress file ---
void compress(const string& input_path, const string& output_path,
               uint32_t seed, bool dummy_mode) {
    ifstream in(input_path, ios::binary);
    if (!in) { cerr << "Error opening input file\n"; return; }
    ofstream out(output_path, ios::binary);
    if (!out) { cerr << "Error creating output file\n"; return; }

    in.seekg(0, ios::end);
    uint32_t total_orig = (uint32_t)in.tellg();
    in.seekg(0, ios::beg);
    out.write((char*)&total_orig, sizeof(total_orig));

    EncryptionKey enc_key;
    enc_key.init_from_seed(seed);

    vector<uint8_t> buffer(BLOCK_SIZE);
    size_t total_comp = sizeof(total_orig);

    while (in) {
        in.read((char*)buffer.data(), BLOCK_SIZE);
        size_t bytes_read = in.gcount();
        if (bytes_read == 0) break;

        vector<uint8_t> comp = compress_block(buffer.data(), bytes_read,
                                               enc_key, dummy_mode);
        uint32_t ob = (uint32_t)bytes_read;
        uint32_t cb = (uint32_t)comp.size();
        out.write((char*)&ob, sizeof(ob));
        out.write((char*)&cb, sizeof(cb));
        out.write((char*)comp.data(), comp.size());
        total_comp += sizeof(ob) + sizeof(cb) + comp.size();
    }

    cout << "Compressed: " << total_orig << " -> " << total_comp << " bytes\n";
}

// --- Decompress file ---
void decompress(const string& input_path, const string& output_path,
                uint32_t seed, bool dummy_mode) {
    ifstream in(input_path, ios::binary);
    if (!in) { cerr << "Error opening compressed file\n"; return; }
    ofstream out(output_path, ios::binary);
    if (!out) { cerr << "Error creating decompressed file\n"; return; }

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

        AdaptiveModel model;
        model.init();
        enc_key.index = 0;

        RansDecSymbol dsyms[256];
        uint8_t slot_to_sym[PROB_SCALE];

        // בנה טבלה ראשונה
        model.buildDecTable(dsyms, slot_to_sym);
        uint32_t next_rebuild = REBUILD_INTERVAL;

        vector<uint8_t> output;
        output.reserve(orig_b);

        for (uint32_t i = 0; i < orig_b; i++) {
            // בנה טבלה מחדש רק בגבולות interval — זהה למקודד
            if (i == next_rebuild) {
                model.buildDecTable(dsyms, slot_to_sym);
                next_rebuild += REBUILD_INTERVAL;
            }

            uint32_t cum = RansDecGet(&rans, PROB_BITS);
            uint8_t  sym = slot_to_sym[cum];
            output.push_back(sym);

            RansDecAdvanceSymbol(&rans, &ptr, &dsyms[sym], PROB_BITS);

            if (enc_key.get_next_bit(dummy_mode))
                model.update(sym);
        }

        out.write((char*)output.data(), output.size());
    }

    cout << "Decompressed to: " << output_path << endl;
}

// --- Main ---
int main(int argc, char** argv) {
    if (argc < 4) {
        cout << "Usage:\n"
             << "  ./compressor.exe c input output [seed] [dummy]\n"
             << "  ./compressor.exe d input output [seed] [dummy]\n";
        return 1;
    }

    string mode   = argv[1];
    string input  = argv[2];
    string output = argv[3];

    uint32_t seed   = 42;    // ברירת מחדל
    bool dummy_mode = false;

    if (argc >= 5) seed       = (uint32_t)stoul(argv[4]);
    if (argc >= 6) dummy_mode = (stoi(argv[5]) == 1);

    vector<uint8_t> dummy_bits; // לא בשימוש יותר
    
    if (mode == "c")
        compress(input, output, seed, dummy_mode);
    else if (mode == "d")
        decompress(input, output, seed, dummy_mode);
    else
        cout << "Unknown mode\n";

    return 0;
}