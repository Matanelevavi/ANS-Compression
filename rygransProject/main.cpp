#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>
#include <cstring>
#include <iomanip>

// ייבוא הספרייה החיצונית המממשת את המתמטיקה של rANS
// ספרייה זו נכתבה על ידי Fabian Giesen ונחשבת לסטנדרט בתחום.
#include "platform.h"
#include "rans_byte.h"

using namespace std;

// --- הגדרות קבועות ---
// PROB_BITS: קובע את דיוק ההסתברות. 14 ביט אומר שהשלם (100%) מחולק ל-16384 חלקים.
// זהו איזון טוב בין דיוק לבין גודל המשתנים בזיכרון.
#define PROB_BITS 14
#define PROB_SCALE (1 << PROB_BITS) // 2 בחזקת 14 = 16384

// --- מבנה נתונים לניהול הסטטיסטיקה ---
// מבנה זה מרכז את כל המידע הדרוש לדחיסה ולפריסה של תו ספציפי.
struct SymbolStats {
    uint32_t freqs[256];      // טבלת תדרים: כמה פעמים מופיע כל תו (0-255) בקובץ
    RansEncSymbol esyms[256]; // סמלים פנימיים לשימוש המקודד (Encoder)
    RansDecSymbol dsyms[256]; // סמלים פנימיים לשימוש המפענח (Decoder)
    uint8_t slot_to_symbol[PROB_SCALE]; // טבלת המרה הפוכה: מציאת התו לפי ההסתברות (עבור ה-Decoder)
};

// --- פונקציית עזר: קריאת קובץ ---
// פונקציה זו קוראת את כל תוכן הקובץ מהדיסק ומחזירה אותו כווקטור של בתים.
vector<uint8_t> load_file(const string& filename) {
    ifstream file(filename, ios::binary | ios::ate); // פתיחה במצב בינארי ומעבר לסוף (כדי לדעת גודל)
    if (!file) {
        cerr << "שגיאה: לא ניתן לפתוח את הקובץ " << filename << endl;
        exit(1);
    }
    streamsize size = file.tellg(); // בדיקת הגודל
    file.seekg(0, ios::beg);        // חזרה להתחלה
    vector<uint8_t> buffer(size);
    if (file.read((char*)buffer.data(), size)) return buffer;
    return {};
}

// --- פונקציית הליבה: נרמול תדרים (Normalization) ---
// תפקיד הפונקציה: להמיר את "מספר המופעים" של כל תו ל"הסתברות מנורמלת".
// סך כל ההסתברויות חייב להגיע בדיוק ל-16384 (PROB_SCALE).
void normalize_frequencies(SymbolStats& stats, uint32_t total_bytes) {
    uint32_t current_sum = 0; // סכום מצטבר (איפה מתחיל הטווח של התו הנוכחי)
    uint32_t prob;            // ההסתברות של התו הנוכחי
    
    // משתנים לשמירת התו האחרון (לצורך תיקון שאריות עיגול)
    int last_sym = -1;
    uint32_t last_prob = 0;
    uint32_t last_start = 0;

    for (int i = 0; i < 256; i++) {
        // אם התו לא קיים בקובץ, מאתחלים אותו כריק
        if (stats.freqs[i] == 0) {
            RansEncSymbolInit(&stats.esyms[i], 0, 0, PROB_BITS); 
            RansDecSymbolInit(&stats.dsyms[i], 0, 0); 
            continue;
        }

        // חישוב ההסתברות: (מספר מופעים / סה"כ בתים) * הסקאלה
        prob = (uint32_t)(((uint64_t)stats.freqs[i] * PROB_SCALE) / total_bytes);
        
        // חוק חשוב: כל תו שקיים חייב לקבל לפחות הסתברות 1, אחרת לא נוכל לקודד אותו
        if (prob == 0) prob = 1; 
        
        // הגנה מפני חריגה מהסקאלה
        if (current_sum + prob > PROB_SCALE) {
            prob = PROB_SCALE - current_sum;
        }
        
        // שמירת הנתונים לתיקון מאוחר
        last_sym = i;
        last_prob = prob;
        last_start = current_sum;

        // אתחול המבנים של ספריית rANS עם הנתונים שחישבנו
        RansEncSymbolInit(&stats.esyms[i], current_sum, prob, PROB_BITS);
        RansDecSymbolInit(&stats.dsyms[i], current_sum, prob);

        // מילוי טבלת ה-Lookup לפענוח מהיר: כל הטווח הזה שייך לתו i
        for (uint32_t j = 0; j < prob; j++) {
            stats.slot_to_symbol[current_sum + j] = (uint8_t)i;
        }

        current_sum += prob;
    }

    // תיקון סופי: אם סכום ההסתברויות יצא פחות מ-16384 (בגלל עיגול כלפי מטה),
    // אנחנו מוסיפים את השארית לתו האחרון כדי לסגור את המעגל המושלם.
    if (current_sum < PROB_SCALE && last_sym != -1) {
        uint32_t remainder = PROB_SCALE - current_sum;
        uint32_t new_prob = last_prob + remainder;
        
        // עדכון מחדש של התו האחרון
        RansEncSymbolInit(&stats.esyms[last_sym], last_start, new_prob, PROB_BITS);
        RansDecSymbolInit(&stats.dsyms[last_sym], last_start, new_prob);

        // עדכון הטבלה ההפוכה
        for(uint32_t k = 0; k < remainder; k++) {
            stats.slot_to_symbol[current_sum + k] = (uint8_t)last_sym;
        }
    }
}

// --- דחיסה (Compress) ---
void compress(const string& input_path, const string& output_path) {
    // 1. טעינת הקובץ
    vector<uint8_t> input = load_file(input_path);
    if (input.empty()) { cout << "קובץ ריק או לא נמצא!" << endl; return; }

    // 2. ניתוח סטטיסטי (Pass 1)
    SymbolStats stats = {0};
    for (uint8_t b : input) stats.freqs[b]++; // ספירת מופעים
    
    // 3. בניית המודל
    normalize_frequencies(stats, input.size());

    // 4. אתחול המקודד
    RansState rans;
    RansEncInit(&rans);

    // הכנת באפר לפלט (מעט גדול יותר מהקלט למקרה שהדחיסה נכשלת או עבור כותרות)
    vector<uint8_t> output_buf(input.size() + 32000); 
    uint8_t* ptr = output_buf.data() + output_buf.size(); // מצביע לסוף (rANS כותב מהסוף להתחלה!)

    // 5. לולאת הדחיסה (Pass 2) - רצים מהסוף להתחלה
    for (size_t i = input.size(); i > 0; i--) {
        uint8_t symbol = input[i - 1];
        RansEncPutSymbol(&rans, &ptr, &stats.esyms[symbol]); // קידוד תו בודד
    }
    RansEncFlush(&rans, &ptr); // סגירת המקודד

    // 6. כתיבה לקובץ דחוס
    // מבנה הקובץ: [גודל מקורי] + [טבלת תדרים] + [מידע דחוס]
    ofstream out(output_path, ios::binary);
    if (!out) { cerr << "שגיאה ביצירת קובץ פלט." << endl; return; }
    
    uint32_t original_size = (uint32_t)input.size();
    out.write((char*)&original_size, sizeof(original_size)); // כתיבת הגודל המקורי
    out.write((char*)stats.freqs, sizeof(stats.freqs));      // כתיבת הטבלה (כדי שנוכל לשחזר)

    size_t compressed_size = (output_buf.data() + output_buf.size()) - ptr;
    out.write((char*)ptr, compressed_size); // כתיבת המידע הדחוס עצמו

    cout << "דחיסה הושלמה:" << endl;
    cout << "מקור: " << original_size << " בתים" << endl;
    cout << "דחוס: " << compressed_size + sizeof(original_size) + sizeof(stats.freqs) << " בתים (כולל כותרת)" << endl;
}

// --- פריסה (Decompress) ---
void decompress(const string& input_path, const string& output_path) {
    ifstream in(input_path, ios::binary);
    if (!in) { cerr << "שגיאה בפתיחת קובץ דחוס." << endl; return; }

    // 1. קריאת הכותרות (Header)
    uint32_t original_size;
    if (!in.read((char*)&original_size, sizeof(original_size))) return;

    SymbolStats stats = {0};
    // קריאת טבלת התדרים שנשמרה בזמן הדחיסה
    if (!in.read((char*)stats.freqs, sizeof(stats.freqs))) return;

    // 2. שחזור המודל הסטטיסטי (חייב להיות זהה ב-100% למודל בדחיסה)
    normalize_frequencies(stats, original_size);

    // 3. קריאת המידע הדחוס לזיכרון
    vector<uint8_t> compressed_data((istreambuf_iterator<char>(in)), {});
    uint8_t* ptr = compressed_data.data();

    // 4. אתחול המפענח
    RansState rans;
    RansDecInit(&rans, &ptr);

    vector<uint8_t> output;
    output.reserve(original_size);

    // 5. לולאת הפענוח
    for (size_t i = 0; i < original_size; i++) {
        // קבלת הערך הנוכחי מהמפענח
        uint32_t cum_freq = RansDecGet(&rans, PROB_BITS);

        // תרגום הערך לתו המקורי באמצעות הטבלה ההפוכה
        uint8_t symbol = stats.slot_to_symbol[cum_freq];

        output.push_back(symbol);

        // קידום המפענח לתו הבא
        RansDecAdvanceSymbol(&rans, &ptr, &stats.dsyms[symbol], PROB_BITS);
    }

    // 6. שמירת הקובץ המשוחזר
    ofstream out(output_path, ios::binary);
    out.write((char*)output.data(), output.size());

    cout << "שוחזר בהצלחה לקובץ: " << output_path << endl;
}

// --- פונקציית ה-Main ---
int main(int argc, char** argv) {
    if (argc < 4) {
        cout << "שימוש בתוכנה:\n";
        cout << "  לדחיסה:  ./compressor c <input_file> <output_file>\n";
        cout << "  לפריסה:  ./compressor d <input_file> <output_file>\n";
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
        cout << "מצב לא מוכר (השתמש ב-c או d)" << endl;
    }

    return 0;