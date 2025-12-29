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
    
    # משתנים לסיכום כולל
    total_orig = 0
    total_ans = 0
    total_ref = 0

    # כותרת טבלה מעודכנת עם גדלים
    print(f"\n{'Filename':<15} | {'Orig (B)':<10} | {'Rygrans(B)':<11} | {'Ref(B)':<10} | {'Your ANS %':<11} | {'Ref Arith %':<12} | {'Gap %'}")
    print("-" * 95)

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

        # בדיקת גדלים
        ans_size = os.path.getsize(out_ans) if os.path.exists(out_ans) else orig_size
        ref_size = os.path.getsize(out_ref) if os.path.exists(out_ref) else orig_size
        
        # צבירה לסיכום
        total_orig += orig_size
        total_ans += ans_size
        total_ref += ref_size

        ans_ratio = calculate_ratio(ans_size, orig_size)
        ref_ratio = calculate_ratio(ref_size, orig_size)
        gap = ans_ratio - ref_ratio

        print(f"{filename:<15} | {orig_size:<10} | {ans_size:<11} | {ref_size:<10} | {ans_ratio:>10.2f}% | {ref_ratio:>11.2f}% | {gap:>+6.2f}%")

        results.append({
            'File Name': filename,
            'Original Size': orig_size,
            'Rygrans Size': ans_size,       # הוספנו גודל
            'Ref Arith Size': ref_size,     # הוספנו גודל
            'Your ANS Ratio (%)': round(ans_ratio, 2),
            'Ref Arith Ratio (%)': round(ref_ratio, 2),
            'Gap (%)': round(gap, 2)
        })

        # ניקוי קבצים זמניים
        if os.path.exists(out_ans): os.remove(out_ans)
        if os.path.exists(out_ref): os.remove(out_ref)

    # --- חישוב שורת סיכום (TOTAL) ---
    tot_ans_ratio = calculate_ratio(total_ans, total_orig)
    tot_ref_ratio = calculate_ratio(total_ref, total_orig)
    tot_gap = tot_ans_ratio - tot_ref_ratio

    print("-" * 95)
    print(f"{'TOTAL':<15} | {total_orig:<10} | {total_ans:<11} | {total_ref:<10} | {tot_ans_ratio:>10.2f}% | {tot_ref_ratio:>11.2f}% | {tot_gap:>+6.2f}%")

    # הוספת שורת הסיכום ל-CSV
    results.append({
        'File Name': 'TOTAL',
        'Original Size': total_orig,
        'Rygrans Size': total_ans,
        'Ref Arith Size': total_ref,
        'Your ANS Ratio (%)': round(tot_ans_ratio, 2),
        'Ref Arith Ratio (%)': round(tot_ref_ratio, 2),
        'Gap (%)': round(tot_gap, 2)
    })

    # שמירה ל-CSV
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    df.to_csv(REPORT_FILE, index=False)
    print(f"\n✅ Done! Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    run_benchmark()