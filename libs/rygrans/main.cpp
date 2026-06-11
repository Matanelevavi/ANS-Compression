#include <iostream>
#include <string>
#include <cstdint>

#include "Compressor.h"
#include "Decompressor.h"

using namespace std;

int main(int argc, char** argv) {
    if (argc < 4) {
        cout << "Usage:\n"
             << "  compressor.exe c <input> <output> [seed] [dummy]\n"
             << "  compressor.exe d <input> <output> [seed] [dummy]\n";
        return 1;
    }

    string   mode   = argv[1];
    string   input  = argv[2];
    string   output = argv[3];

    if      (mode == "c") compress  (input, output);
    else if (mode == "d") decompress(input, output);
    else    cerr << "Unknown mode '" << mode << "' (use c or d)\n";

    return 0;
}
