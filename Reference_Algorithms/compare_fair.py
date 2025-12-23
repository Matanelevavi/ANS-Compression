import os
import subprocess
import pandas as pd

# --- הגדרות ---
MY_COMPRESSOR = "compressor.exe"
# נתיב לדוחס הפשוט יותר שקימפלנו הרגע
REF_COMPRESSOR = os.path.join("reference_arith_simple", "arith_simple.exe")
TEST_DIR = "cantrbry"
REPORT_FILE = "Fair_Comparison_Report.csv"

def get_file_size(path):
    return os.path.getsize(path) if os.path.exists(path) else 0

def run_benchmark():
    if not os.path.exists(MY_COMPRESSOR):
        print(f"Error: Your compressor '{MY_COMPRESSOR}' is missing!")
        return
    if not os.path.exists(REF_COMPRESSOR):
        print(f"Error: Reference compressor '{REF_COMPRESSOR}' is missing!")
        print("Please compile arith_simple.exe first!")
        return

    results = []
    # סינון קבצים בלבד
    files = [f for f in os.listdir(TEST_DIR) if os.path.isfile(os.path.join(TEST_DIR, f))]
    
    print(f"{'Filename':<15} | {'Orig':<8} | {'ANS (You)':<10} | {'Arith(0)':<10} | {'Gap':<8}")
    print("-" * 65)

    for filename in files:
        filepath = os.path.join(TEST_DIR, filename)
        out_ans = filepath + ".my_ans"
        out_ref = filepath + ".ref_arith"
        
        orig_size = get_file_size(filepath)
        
        # 1. ANS (שלך)
        try:
            subprocess.run([MY_COMPRESSOR, "c", filepath, out_ans], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e: print(f"Error ANS: {e}")

        # 2. Arithmetic Order-0 (של הרפרנס)
        try:
            subprocess.run([REF_COMPRESSOR, filepath, out_ref], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e: print(f"Error Ref: {e}")

        ans_size = get_file_size(out_ans)
        ref_size = get_file_size(out_ref)
        
        # Gap calculation
        diff = ans_size - ref_size 
        
        print(f"{filename:<15} | {orig_size:<8} | {ans_size:<10} | {ref_size:<10} | {diff:<+8}")

        results.append({
            'File Name': filename,
            'Original': orig_size,
            'Your ANS': ans_size,
            'Arith Order-0': ref_size,
            'Diff (Bytes)': diff
        })

        # ניקוי קבצים זמניים
        if os.path.exists(out_ans): os.remove(out_ans)
        if os.path.exists(out_ref): os.remove(out_ref)

    # שמירת הדוח
    df = pd.DataFrame(results)
    df.to_csv(REPORT_FILE, index=False)
    print(f"\nDone! Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    run_benchmark()