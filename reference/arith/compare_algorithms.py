import os
import subprocess
import pandas as pd

# --- הגדרות ---
MY_COMPRESSOR = "compressor.exe"
# הנתיב לקובץ הרפרנס (בתוך התיקייה הפנימית)
REF_COMPRESSOR = os.path.join("reference_arith", "arith_n.exe")
TEST_DIR = "cantrbry"
REPORT_FILE = "Final_Comparison_Report.csv"

def get_file_size(path):
    return os.path.getsize(path) if os.path.exists(path) else 0

def run_benchmark():
    if not os.path.exists(MY_COMPRESSOR):
        print(f"Error: Your compressor '{MY_COMPRESSOR}' is missing!")
        return
    if not os.path.exists(REF_COMPRESSOR):
        print(f"Error: Reference compressor '{REF_COMPRESSOR}' is missing!")
        return

    results = []
    # סינון תיקיות וקבצים לא רלוונטיים
    files = [f for f in os.listdir(TEST_DIR) if os.path.isfile(os.path.join(TEST_DIR, f))]

    print(f"{'Filename':<15} | {'Orig':<8} | {'ANS (You)':<10} | {'Arith (Ref)':<10} | {'Gap':<8}")
    print("-" * 65)

    for filename in files:
        filepath = os.path.join(TEST_DIR, filename)
        out_ans = filepath + ".my_ans"
        out_ref = filepath + ".ref_arith"

        orig_size = get_file_size(filepath)

        # 1. הרצת ה-ANS שלך
        try:
            subprocess.run([MY_COMPRESSOR, "c", filepath, out_ans], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error ANS: {e}")

        # 2. הרצת הרפרנס (Arithmetic N)
        try:
            subprocess.run([REF_COMPRESSOR, filepath, out_ref], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error Ref: {e}")

        ans_size = get_file_size(out_ans)
        ref_size = get_file_size(out_ref)

        # חישוב אחוזי חיסכון
        ans_saving = (1 - ans_size / orig_size) * 100 if orig_size > 0 else 0
        ref_saving = (1 - ref_size / orig_size) * 100 if orig_size > 0 else 0

        # חיובי = הרפרנס ניצח, שלילי = אתה ניצחת
        diff = ans_size - ref_size 

        print(f"{filename:<15} | {orig_size:<8} | {ans_size:<10} | {ref_size:<10} | {diff:<+8}")

        results.append({
            'File Name': filename,
            'Original': orig_size,
            'Your ANS': ans_size,
            'Ref Arith': ref_size,
            'Your Savings %': round(ans_saving, 2),
            'Ref Savings %': round(ref_saving, 2),
            'Diff (Bytes)': diff
        })

        if os.path.exists(out_ans): os.remove(out_ans)
        if os.path.exists(out_ref): os.remove(out_ref)

    # שמירה לקובץ
    df = pd.DataFrame(results)
    df.to_csv(REPORT_FILE, index=False)
    print(f"\nDone! Comparison saved to {REPORT_FILE}")

if __name__ == "__main__":
    run_benchmark()