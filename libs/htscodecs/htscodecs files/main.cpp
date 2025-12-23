#include <iostream>
#include <fstream>
#include <vector>
#include <cstring>
#include <cstdlib> // עבור free

// הגדרות כדי לעבוד עם קוד C
extern "C" {
    #include "rANS_static.h"
}

using namespace std;

vector<uint8_t> load_file(const string& filename) {
    ifstream file(filename, ios::binary | ios::ate);
    if (!file) { cerr << "Error opening " << filename << endl; exit(1); }
    streamsize size = file.tellg();
    file.seekg(0, ios::beg);
    vector<uint8_t> buffer(size);
    if (file.read((char*)buffer.data(), size)) return buffer;
    return {};
}

void compress(const string& input_path, const string& output_path) {
    // 1. טעינת מידע
    vector<uint8_t> input = load_file(input_path);
    if (input.empty()) return;

    // 2. ביצוע הדחיסה (התיקון הגדול)
    unsigned int compressed_sz = 0;
    
    // הפונקציה rans_compress מקצה זיכרון בעצמה ומחזירה מצביע אליו
    // הפרמטר השלישי הוא *מצביע למשתנה* שיחזיק את הגודל הסופי
    unsigned char* compressed_data = rans_compress(
        input.data(),       // המידע המקורי
        input.size(),       // הגודל המקורי
        &compressed_sz,     // הכתובת שבה יישמר הגודל החדש
        0                   // Order-0
    );

    if (!compressed_data) {
        cerr << "Compression failed!" << endl;
        return;
    }

    // 3. שמירה לקובץ
    ofstream out(output_path, ios::binary);
    
    // שמירת הגודל המקורי
    uint32_t orig_size = (uint32_t)input.size();
    out.write((char*)&orig_size, sizeof(orig_size));
    
    // שמירת המידע הדחוס
    out.write((char*)compressed_data, compressed_sz);

    // 4. שחרור הזיכרון שהספרייה הקצתה
    free(compressed_data);

    cout << "Compressed: " << input.size() << " -> " << compressed_sz + 4 << endl;
}

void decompress(const string& input_path, const string& output_path) {
    ifstream in(input_path, ios::binary);
    if (!in) { cerr << "Error opening input" << endl; return; }

    // 1. קריאת הגודל המקורי
    uint32_t original_size;
    if (!in.read((char*)&original_size, sizeof(original_size))) return;

    // 2. קריאת המידע הדחוס
    vector<uint8_t> compressed_data((istreambuf_iterator<char>(in)), {});

    // 3. ביצוע הפריסה
    unsigned int res_size = original_size; 
    
    unsigned char* res = rans_uncompress(
        compressed_data.data(), 
        compressed_data.size(), 
        &res_size
    );

    if (!res) {
        cerr << "Decompression failed!" << endl;
        return;
    }

    // 4. שמירה
    ofstream out(output_path, ios::binary);
    out.write((char*)res, res_size);
    
    free(res);

    cout << "Decompressed to: " << output_path << endl;
}

int main(int argc, char** argv) {
    if (argc < 4) {
        cout << "Usage: ./compressor_static c/d input output\n";
        return 1;
    }
    string mode = argv[1];
    if (mode == "c") compress(argv[2], argv[3]);
    else if (mode == "d") decompress(argv[2], argv[3]);
    return 0;
}