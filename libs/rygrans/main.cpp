#define NOMINMAX // מונע התנגשויות שמות בווינדוס
#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>
#include <cstring>
#include <iomanip>

#include "platform.h"
#include "rans_byte.h"

using namespace std;

// --- הגדרות ---
#define PROB_BITS 14
#define PROB_SCALE (1 << PROB_BITS)

struct SymbolStats {
    uint32_t freqs[256];
    RansEncSymbol esyms[256];
    RansDecSymbol dsyms[256];
    uint8_t slot_to_symbol[PROB_SCALE];
};

// טעינת קובץ לזיכרון
vector<uint8_t> load_file(const string& filename) {
    ifstream file(filename, ios::binary | ios::ate);
    if (!file) {
        cerr << "Error: Cannot open " << filename << endl;
        exit(1);
    }
    streamsize size = file.tellg();
    file.seekg(0, ios::beg);
    vector<uint8_t> buffer(size);
    if (file.read((char*)buffer.data(), size)) return buffer;
    return {};
}

// נרמול תדרים להסתברויות
void normalize_frequencies(SymbolStats& stats, uint32_t total_bytes) {
    uint32_t norm[256] = {0};
    uint32_t sum = 0;


    // שלב 1: נרמול ראשוני + הבטחת מינימום 1 לכל סימן שמופיע
    for (int i = 0; i < 256; i++) {
        if (stats.freqs[i] > 0) {
            uint32_t p = (uint32_t)(((uint64_t)stats.freqs[i] * PROB_SCALE) / total_bytes);
            if (p == 0) {
                p = 1;
            }
            norm[i] = p;
            sum += p;
        }
    }

    // שלב 2: אם הסכום גדול מדי, מורידים רק מסימנים עם norm > 1
    while (sum > PROB_SCALE) {
        int best = -1;
        uint32_t best_freq = 0;

        for (int i = 0; i < 256; i++) {
            if (norm[i] > 1 && stats.freqs[i] > best_freq) {
                best_freq = stats.freqs[i];
                best = i;
            }
        }

        if (best == -1) {
            cerr << "Normalization error: cannot reduce frequencies safely." << endl;
            exit(1);
        }

        norm[best]--;
        sum--;
    }


    // שלב 3: אם הסכום קטן מדי, מוסיפים לסימן הכי שכיח
    while (sum < PROB_SCALE) {
        int best = -1;
        uint32_t best_freq = 0;

        for (int i = 0; i < 256; i++) {
            if (stats.freqs[i] > best_freq) {
                best_freq = stats.freqs[i];
                best = i;
            }
        }

        if (best == -1) {
            cerr << "Normalization error: no symbol available to increase." << endl;
            exit(1);
        }

        norm[best]++;
        sum++;
    }


    // שלב 4: בניית טבלאות הקידוד/פענוח
    uint32_t start = 0;

    for (int i = 0; i < 256; i++) {
        if (norm[i] == 0) {
            RansEncSymbolInit(&stats.esyms[i], 0, 0, PROB_BITS);
            RansDecSymbolInit(&stats.dsyms[i], 0, 0);
            continue;
        }

        RansEncSymbolInit(&stats.esyms[i], start, norm[i], PROB_BITS);
        RansDecSymbolInit(&stats.dsyms[i], start, norm[i]);

        for (uint32_t j = 0; j < norm[i]; j++) {
            stats.slot_to_symbol[start + j] = (uint8_t)i;
        }

        start += norm[i];
    }
}

// דחיסה
void compress(const string& input_path, const string& output_path) {
    vector<uint8_t> input = load_file(input_path);

    if (input.empty()) {
        cout << "Empty input file!" << endl;
        return;
    }

    // חישוב סטטיסטיקה
    SymbolStats stats = {0};
    for (uint8_t b : input) {
        stats.freqs[b]++;
    }

    normalize_frequencies(stats, input.size());

    RansState rans;
    RansEncInit(&rans);

    vector<uint8_t> output_buf(input.size() * 6 + 1048576);
    uint8_t* ptr = output_buf.data() + output_buf.size();


    // קידוד הפוך
    for (size_t i = input.size(); i > 0; i--) {
        uint8_t symbol = input[i - 1];

        RansEncPutSymbol(&rans, &ptr, &stats.esyms[symbol]);

    }

    RansEncFlush(&rans, &ptr);

    ofstream out(output_path, ios::binary);
    if (!out) {
        cerr << "Error creating output file." << endl;
        return;
    }

    uint32_t original_size = (uint32_t)input.size();

    out.write((char*)&original_size, sizeof(original_size));
    out.write((char*)stats.freqs, sizeof(stats.freqs));

    size_t compressed_size = (output_buf.data() + output_buf.size()) - ptr;
    out.write((char*)ptr, compressed_size);

    cout << "Compressed: " << original_size << " -> "
         << compressed_size + sizeof(original_size) + sizeof(stats.freqs) << endl;
}

// פריסה
void decompress(const string& input_path, const string& output_path) {
    ifstream in(input_path, ios::binary);
    if (!in) { cerr << "Error opening input file." << endl; return; }

    uint32_t original_size;
    if (!in.read((char*)&original_size, sizeof(original_size))) return;

    SymbolStats stats = {0};
    if (!in.read((char*)stats.freqs, sizeof(stats.freqs))) return;

    normalize_frequencies(stats, original_size);

    vector<uint8_t> compressed_data((istreambuf_iterator<char>(in)), {});
    uint8_t* ptr = compressed_data.data();

    RansState rans;
    RansDecInit(&rans, &ptr);

    vector<uint8_t> output;
    output.reserve(original_size);

    for (size_t i = 0; i < original_size; i++) {
        uint32_t cum_freq = RansDecGet(&rans, PROB_BITS);
        uint8_t symbol = stats.slot_to_symbol[cum_freq];
        output.push_back(symbol);
        RansDecAdvanceSymbol(&rans, &ptr, &stats.dsyms[symbol], PROB_BITS);
    }

    ofstream out(output_path, ios::binary);
    out.write((char*)output.data(), output.size());
    cout << "Decompressed to: " << output_path << endl;
}

int main(int argc, char** argv) {
    if (argc < 4) {
        cout << "Usage:\n";
        cout << "  Compress:   ./compressor.exe c <input> <output>\n";
        cout << "  Decompress: ./compressor.exe d <input> <output>\n";
        return 1;
    }

    string mode = argv[1];
    string input = argv[2];
    string output = argv[3];

    if (mode == "c") {
        compress(input, output);
    } else if (mode == "d") {
        decompress(input, output);
    } else {
        cout << "Unknown mode (use c or d)" << endl;
    }

    return 0;
} 