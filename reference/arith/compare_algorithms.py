import os
import subprocess
import pandas as pd

# --- ניהול נתיבים חכם ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# קבצי הרצה
MY_COMPRESSOR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "libs", "rygrans", "compressor.exe"))
REF_COMPRESSOR = os.path.join(BASE_DIR, "reference_arith_simple", "arith_simple.exe")

# תיקיות קלט
CORPUS_SMALL = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "corpus", "cantrbry"))
CORPUS_LARGE = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "corpus", "50MFiles"))

# קבצי פלט/קלט
REPORT_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "results", "Final_Comparison_Report.csv"))
HTS_REPORT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "results", "HTSCodecs_Results.csv"))


def calculate_ratio(compressed_size, original_size):
    """מחשב את אחוז הדחיסה - כמה אחוז הקובץ הדחוס מהמקור"""
    if original_size == 0:
        return 0
    return (compressed_size / original_size) * 100


def process_dataset(dataset_name, corpus_dir, results):
    if not os.path.exists(corpus_dir):
        print(f"Error: Corpus directory not found for {dataset_name}: {corpus_dir}")
        return

    files = [f for f in os.listdir(corpus_dir) if os.path.isfile(os.path.join(corpus_dir, f))]

    print(f"\n=== Dataset: {dataset_name} ===")
    print(f"{'Filename':<20} | {'Orig (B)':<12} | {'Rygrans %':<10} | {'Arith %':<10}")
    print("-" * 65)

    for filename in files:
        filepath = os.path.join(corpus_dir, filename)
        out_ans = filename + ".my_ans"
        out_ref = filename + ".ref_arith"

        orig_size = os.path.getsize(filepath)

        # הרצת הדוחס שלכן
        subprocess.run(
            [MY_COMPRESSOR, "c", filepath, out_ans],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # הרצת דוחס הרפרנס
        subprocess.run(
            [REF_COMPRESSOR, filepath, out_ref],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        ans_size = os.path.getsize(out_ans) if os.path.exists(out_ans) else orig_size
        ref_size = os.path.getsize(out_ref) if os.path.exists(out_ref) else orig_size

        ans_ratio = calculate_ratio(ans_size, orig_size)
        ref_ratio = calculate_ratio(ref_size, orig_size)

        print(f"{filename:<20} | {orig_size:<12} | {ans_ratio:>8.2f}% | {ref_ratio:>8.2f}%")

        results.append({
            'Dataset': dataset_name,
            'File Name': filename,
            'Original Size': orig_size,
            'Rygrans ANS Ratio (%)': round(ans_ratio, 2),
            'Ref Arith Ratio (%)': round(ref_ratio, 2)
        })

        if os.path.exists(out_ans):
            os.remove(out_ans)
        if os.path.exists(out_ref):
            os.remove(out_ref)


def run_benchmark():
    print(f"Using Rygrans compressor: {MY_COMPRESSOR}")

    if not os.path.exists(MY_COMPRESSOR):
        print(f"Error: Missing Rygrans compressor at {MY_COMPRESSOR}")
        return
    if not os.path.exists(REF_COMPRESSOR):
        print(f"Error: Missing Arithmetic reference compressor at {REF_COMPRESSOR}")
        return
    if not os.path.exists(HTS_REPORT):
        print(f"Error: Missing HTS results file at {HTS_REPORT}")
        return

    results = []

    # שלב 1: יצירת טבלת Rygrans + Arithmetic
    process_dataset("cantrbry", CORPUS_SMALL, results)
    process_dataset("50MFiles", CORPUS_LARGE, results)

    df_main = pd.DataFrame(results)

    # שלב 2: טעינת תוצאות HTS
    df_hts = pd.read_csv(HTS_REPORT)
    df_hts.columns = df_hts.columns.str.strip()

    df_hts = df_hts.rename(columns={
        'Dataset': 'Dataset',
        'Filename': 'File Name',
        'Ratio_Percent': 'HTSCodecs ANS Ratio (%)'
    })

    # אם יש שורת TOTAL ב-HTS, נסיר
    if 'Dataset' in df_hts.columns:
        df_hts = df_hts[df_hts['Dataset'] != 'TOTAL']

    needed_hts_cols = ['Dataset', 'File Name', 'HTSCodecs ANS Ratio (%)']
    df_hts = df_hts[needed_hts_cols]

    # שלב 3: מיזוג כל שלושת האלגוריתמים
    merged_df = pd.merge(
        df_main,
        df_hts,
        on=['Dataset', 'File Name'],
        how='inner'
    )

    # שלב 4: חישוב פערים
    merged_df['Gap Rygrans vs Arith (%)'] = (
        merged_df['Rygrans ANS Ratio (%)'] - merged_df['Ref Arith Ratio (%)']
    ).round(2)

    merged_df['Gap Rygrans vs HTS (%)'] = (
        merged_df['Rygrans ANS Ratio (%)'] - merged_df['HTSCodecs ANS Ratio (%)']
    ).round(2)

    merged_df['Gap HTS vs Arith (%)'] = (
        merged_df['HTSCodecs ANS Ratio (%)'] - merged_df['Ref Arith Ratio (%)']
    ).round(2)

    # סדר עמודות סופי
    final_cols = [
        'Dataset',
        'File Name',
        'Original Size',
        'Rygrans ANS Ratio (%)',
        'HTSCodecs ANS Ratio (%)',
        'Ref Arith Ratio (%)',
        'Gap Rygrans vs Arith (%)',
        'Gap Rygrans vs HTS (%)',
        'Gap HTS vs Arith (%)'
    ]

    merged_df = merged_df[final_cols]

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    merged_df.to_csv(REPORT_FILE, index=False)

    print(f"\nDone! Final comparison report saved to: {REPORT_FILE}")


if __name__ == "__main__":
    run_benchmark()