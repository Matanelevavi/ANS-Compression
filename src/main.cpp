#include <iostream>
#include <vector>
#include <string>

// ייבוא הספריות מהמיקומים החדשים שלהן
extern "C" {
    #include "../libs/htscodecs/rANS_static.h"
}
#include "../libs/rygrans/rans_byte.h"
#include "../libs/rygrans/platform.h"

using namespace std;

int main() {
    cout << "--- ANS Compression Benchmark Tool ---" << endl;
    
    // רשימת קבצים לבדיקה מה-Corpus
    vector<string> test_files = {
        "../corpus/cantrbry/alice29.txt",
        "../corpus/cantrbry/asyoulik.txt",
        "../corpus/cantrbry/lcet10.txt"
    };

    for (const string& file_path : test_files) {
        cout << "\nTesting file: " << file_path << endl;
        // כאן נוסיף בהמשך את הלוגיקה שמודדת זמן וגודל דחיסה
    }

    return 0;
}