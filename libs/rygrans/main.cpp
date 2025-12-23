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
    uint32_t current_sum = 0;
    uint32_t prob;
    
    int last_sym = -1;
    uint32_t last_prob = 0;
    uint32_t last_start = 0;

    for (int i = 0; i < 256; i++) {
        if (stats.freqs[i] == 0) {
            RansEncSymbolInit(&stats.esyms[i], 0, 0, PROB_BITS); 
            RansDecSymbolInit(&stats.dsyms[i], 0, 0); 
            continue;
        }

        prob = (uint32_t)(((uint64_t)stats.freqs[i] * PROB_SCALE) / total_bytes);
        if (prob == 0) prob = 1; 
        
        if (current_sum + prob > PROB_SCALE) {
            prob = PROB_SCALE - current_sum;
        }
        
        last_sym = i;
        last_prob = prob;
        last_start = current_sum;

        RansEncSymbolInit(&stats.esyms[i], current_sum, prob, PROB_BITS);
        RansDecSymbolInit(&stats.dsyms[i], current_sum, prob);

        for (uint32_t j = 0; j < prob; j++) {
            stats.slot_to_symbol[current_sum + j] = (uint8_t)i;
        }

        current_sum += prob;
    }

    if (current_sum < PROB_SCALE && last_sym != -1) {
        uint32_t remainder = PROB_SCALE - current_sum;
        uint32_t new_prob = last_prob + remainder;
        
        RansEncSymbolInit(&stats.esyms[last_sym], last_start, new_prob, PROB_BITS);
        RansDecSymbolInit(&stats.dsyms[last_sym], last_start, new_prob);

        for(uint32_t k = 0; k < remainder; k++) {
            stats.slot_to_symbol[current_sum + k] = (uint8_t)last_sym;
        }
    }
}

// דחיסה
void compress(const string& input_path, const string& output_path) {
    vector<uint8_t> input = load_file(input_path);
    if (input.empty()) { cout << "Empty input file!" << endl; return; }

    // חישוב סטטיסטיקה
    SymbolStats stats = {0};
    for (uint8_t b : input) stats.freqs[b]++;
    
    normalize_frequencies(stats, input.size());

    RansState rans;
    RansEncInit(&rans);

    vector<uint8_t> output_buf(input.size() + 32000); 
    uint8_t* ptr = output_buf.data() + output_buf.size();

    // קידוד הפוך
    for (size_t i = input.size(); i > 0; i--) {
        uint8_t symbol = input[i - 1];
        RansEncPutSymbol(&rans, &ptr, &stats.esyms[symbol]);
    }
    RansEncFlush(&rans, &ptr);

    ofstream out(output_path, ios::binary);
    if (!out) { cerr << "Error creating output file." << endl; return; }
    
    uint32_t original_size = (uint32_t)input.size();
    
    // כתיבת Header
    out.write((char*)&original_size, sizeof(original_size));
    // כאן נכתבת הטבלה הגדולה (1024 בתים). זה תקין לבינתיים.
    out.write((char*)stats.freqs, sizeof(stats.freqs));

    size_t compressed_size = (output_buf.data() + output_buf.size()) - ptr;
    out.write((char*)ptr, compressed_size);

    cout << "Compressed: " << original_size << " -> " << compressed_size + sizeof(original_size) + sizeof(stats.freqs) << endl;
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