import os
import subprocess
import pandas as pd

# --- ניהול נתיבים חכם ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# נתיבים מוחלטים יחסית למיקום הסקריפט
MY_COMPRESSOR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "libs", "rygrans", "compressor.exe"))
REF_COMPRESSOR = os.path.join(BASE_DIR, "reference_arith_simple", "arith_simple.exe")
CORPUS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "corpus", "cantrbry"))
REPORT_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "results", "Final_Comparison_Report.csv"))

def calculate_ratio(compressed_size, original_size):
    """מחשב את אחוז הדחיסה - כמה אחוז הקובץ הדחוס מהמקור"""
    if original_size == 0:
        return 0
    return (compressed_size / original_size) * 100

def run_benchmark():
    print(f"DEBUG: Looking for compressor at: {MY_COMPRESSOR}")
    
    if not os.path.exists(MY_COMPRESSOR):
        print(f"❌ Error: Your compressor is missing at {MY_COMPRESSOR}!")
        return
    if not os.path.exists(REF_COMPRESSOR):
        print(f"❌ Error: Reference compressor is missing at {REF_COMPRESSOR}!")
        return
    if not os.path.exists(CORPUS_DIR):
        print(f"❌ Error: Corpus directory not found at {CORPUS_DIR}!")
        return

    results = []
    files = [f for f in os.listdir(CORPUS_DIR) if os.path.isfile(os.path.join(CORPUS_DIR, f))]
    
    print(f"\n{'Filename':<15} | {'Orig (B)':<10} | {'Your ANS %':<12} | {'Ref Arith %':<12} | {'Gap %'}")
    print("-" * 70)

    for filename in files:
        filepath = os.path.join(CORPUS_DIR, filename)
        out_ans = filename + ".my_ans"
        out_ref = filename + ".ref_arith"
        
        orig_size = os.path.getsize(filepath)
        
        # הרצת הדוחס שלך
        subprocess.run([MY_COMPRESSOR, "c", filepath, out_ans], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # הרצת דוחס הרפרנס
        subprocess.run([REF_COMPRESSOR, filepath, out_ref], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # בדיקת גדלים (אם הקובץ לא נוצר, נחשב כ-100%)
        ans_size = os.path.getsize(out_ans) if os.path.exists(out_ans) else orig_size
        ref_size = os.path.getsize(out_ref) if os.path.exists(out_ref) else orig_size
        
        ans_ratio = calculate_ratio(ans_size, orig_size)
        ref_ratio = calculate_ratio(ref_size, orig_size)
        gap = ans_ratio - ref_ratio

        print(f"{filename:<15} | {orig_size:<10} | {ans_ratio:>10.2f}% | {ref_ratio:>11.2f}% | {gap:>+6.2f}%")

        results.append({
            'File Name': filename,
            'Original Size': orig_size,
            'Your ANS Ratio (%)': round(ans_ratio, 2),
            'Ref Arith Ratio (%)': round(ref_ratio, 2),
            'Gap (%)': round(gap, 2)
        })

        # ניקוי קבצים זמניים
        if os.path.exists(out_ans): os.remove(out_ans)
        if os.path.exists(out_ref): os.remove(out_ref)

    # שמירה ל-CSV
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    df.to_csv(REPORT_FILE, index=False)
    print(f"\n✅ Done! Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    run_benchmark()