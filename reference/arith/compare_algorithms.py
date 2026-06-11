import os
import subprocess
import pandas as pd

# --- Smart Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Compressors
MY_COMPRESSOR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "libs", "rygrans", "compressor.exe")
)

REF_COMPRESSOR = os.path.join(
    BASE_DIR,
    "reference_arith_simple",
    "arith_simple.exe"
)

# files Directories
FILES_SMALL = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "files", "smallFiles")
)

FILES_LARGE = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "files", "50MFiles")
)

# Output Report
REPORT_FILE = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "results", "Final_Comparison_Report.csv")
)


def calculate_ratio(compressed_size, original_size):
    """Compression ratio percentage"""

    if original_size == 0:
        return 0

    return (compressed_size / original_size) * 100


def process_dataset(dataset_name, files_dir, results):

    if not os.path.exists(files_dir):
        print(f"Error: Missing dataset directory: {files_dir}")
        return

    files = [
        f for f in os.listdir(files_dir)
        if os.path.isfile(os.path.join(files_dir, f))
    ]

    print(f"\n=== Dataset: {dataset_name} ===")

    print(
        f"{'Filename':<20} | "
        f"{'Orig (B)':<12} | "
        f"{'Rygrans %':<12} | "
        f"{'Arith %':<12}"
    )

    print("-" * 70)

    for filename in files:

        filepath = os.path.join(files_dir, filename)

        out_ans = filename + ".my_ans"
        out_ref = filename + ".ref_arith"

        orig_size = os.path.getsize(filepath)

        # Run Rygrans
        subprocess.run(
            [MY_COMPRESSOR, "c", filepath, out_ans],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Run Arithmetic Reference
        subprocess.run(
            [REF_COMPRESSOR, filepath, out_ref],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        ans_size = (
            os.path.getsize(out_ans)
            if os.path.exists(out_ans)
            else orig_size
        )

        ref_size = (
            os.path.getsize(out_ref)
            if os.path.exists(out_ref)
            else orig_size
        )

        ans_ratio = calculate_ratio(ans_size, orig_size)
        ref_ratio = calculate_ratio(ref_size, orig_size)

        print(
            f"{filename:<20} | "
            f"{orig_size:<12} | "
            f"{ans_ratio:>8.2f}% | "
            f"{ref_ratio:>8.2f}%"
        )

        results.append({
            'Dataset': dataset_name,
            'File Name': filename,

            'Original Size (B)': orig_size,

            'Rygrans Size (B)': ans_size,
            'Arithmetic Size (B)': ref_size,

            'Rygrans Ratio (%)': round(ans_ratio, 2),
            'Arithmetic Ratio (%)': round(ref_ratio, 2),

            'Difference (%)': round(ans_ratio - ref_ratio, 2)
        })

        # Cleanup
        if os.path.exists(out_ans):
            os.remove(out_ans)

        if os.path.exists(out_ref):
            os.remove(out_ref)


def run_benchmark():

    print(f"Using Rygrans compressor: {MY_COMPRESSOR}")

    if not os.path.exists(MY_COMPRESSOR):
        print(f"Error: Missing Rygrans compressor")
        return

    if not os.path.exists(REF_COMPRESSOR):
        print(f"Error: Missing arithmetic reference compressor")
        return

    results = []

    process_dataset("smallFiles", FILES_SMALL, results)
    process_dataset("50MFiles", FILES_LARGE, results)

    df = pd.DataFrame(results)

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

    df.to_csv(REPORT_FILE, index=False)

    print(f"\nFinal report saved to:")
    print(REPORT_FILE)


if __name__ == "__main__":
    run_benchmark()