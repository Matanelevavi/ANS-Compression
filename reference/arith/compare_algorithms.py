"""
compare_algorithms.py - compare the rANS engine to the arithmetic
coding baseline on both datasets.

The baseline is an order-0 adaptive arithmetic coder (arith.c from
Mark Nelson's "The Data Compression Book"), the same family of coder
used as the starting point in the Klein & Shapira paper.

Output: results/Final_Comparison_Report.csv
"""

import os
import platform
import subprocess
import sys
import tempfile

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

IS_WINDOWS = platform.system() == "Windows"

RYGRANS_DIR   = os.path.join(ROOT_DIR, "libs", "rygrans")
MY_COMPRESSOR = os.path.join(RYGRANS_DIR,
                             "compressor.exe" if IS_WINDOWS else "compressor")

ARITH_DIR      = os.path.join(BASE_DIR, "reference_arith_simple")
REF_COMPRESSOR = os.path.join(ARITH_DIR,
                              "arith_simple.exe" if IS_WINDOWS else "arith_simple")

FILES_SMALL = os.path.join(ROOT_DIR, "files", "smallFiles")
FILES_LARGE = os.path.join(ROOT_DIR, "files", "50MFiles")

REPORT_FILE = os.path.join(ROOT_DIR, "results", "Final_Comparison_Report.csv")


def build_arith():
    """Compile the arithmetic coding baseline if it is missing."""
    if os.path.exists(REF_COMPRESSOR):
        return
    sources = [os.path.join(ARITH_DIR, s)
               for s in ("main-c.c", "arith.c", "bitio.c", "errhand.c")]
    cmd = ["gcc", "-O2"] + sources + ["-o", REF_COMPRESSOR]
    print("Building arithmetic baseline...")
    result = subprocess.run(cmd, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stderr.decode(errors="replace"))
        print("Build of the arithmetic baseline failed.")
        sys.exit(1)


def ratio_percent(compressed_size, original_size):
    if original_size == 0:
        return 0.0
    return compressed_size / original_size * 100


def process_dataset(dataset_name, files_dir, results, temp_dir):
    if not os.path.isdir(files_dir):
        print(f"[Warning] dataset directory missing: {files_dir}")
        return

    files = sorted(f for f in os.listdir(files_dir)
                   if os.path.isfile(os.path.join(files_dir, f))
                   and not f.endswith(".py"))  # skip tooling scripts, e.g. download_corpus.py

    print(f"\n=== Dataset: {dataset_name} ===")
    print(f"{'Filename':<20} | {'Orig (B)':<12} | {'Rygrans %':<10} | {'Arith %':<10}")
    print("-" * 62)

    for filename in files:
        filepath = os.path.join(files_dir, filename)
        out_ans  = os.path.join(temp_dir, filename + ".my_ans")
        out_ref  = os.path.join(temp_dir, filename + ".ref_arith")
        orig_size = os.path.getsize(filepath)

        try:
            subprocess.run([MY_COMPRESSOR, "c", filepath, out_ans],
                           stdout=subprocess.DEVNULL, check=True)
            subprocess.run([REF_COMPRESSOR, filepath, out_ref],
                           stdout=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            print(f"{filename:<20} | COMPRESSOR FAILED (exit {e.returncode})")
            results.append({
                "Dataset": dataset_name, "File Name": filename,
                "Original Size (B)": orig_size,
                "Rygrans Size (B)": None, "Arithmetic Size (B)": None,
                "Rygrans Ratio (%)": None, "Arithmetic Ratio (%)": None,
                "Difference (%)": None, "Status": "FAILED",
            })
            continue

        ans_size = os.path.getsize(out_ans)
        ref_size = os.path.getsize(out_ref)
        ans_ratio = ratio_percent(ans_size, orig_size)
        ref_ratio = ratio_percent(ref_size, orig_size)

        print(f"{filename:<20} | {orig_size:<12} | "
              f"{ans_ratio:>8.2f}% | {ref_ratio:>8.2f}%")

        results.append({
            "Dataset": dataset_name, "File Name": filename,
            "Original Size (B)": orig_size,
            "Rygrans Size (B)": ans_size, "Arithmetic Size (B)": ref_size,
            "Rygrans Ratio (%)": round(ans_ratio, 2),
            "Arithmetic Ratio (%)": round(ref_ratio, 2),
            "Difference (%)": round(ans_ratio - ref_ratio, 2),
            "Status": "OK",
        })

        for p in (out_ans, out_ref):
            if os.path.exists(p):
                os.remove(p)


def main():
    if not os.path.exists(MY_COMPRESSOR):
        print(f"Rygrans compressor not found: {MY_COMPRESSOR}")
        print("Run libs/rygrans/run_benchmark.py first (it builds it).")
        sys.exit(1)

    build_arith()

    results = []
    with tempfile.TemporaryDirectory(prefix="ans_compare_") as temp_dir:
        process_dataset("smallFiles", FILES_SMALL, results, temp_dir)
        process_dataset("50MFiles", FILES_LARGE, results, temp_dir)

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    pd.DataFrame(results).to_csv(REPORT_FILE, index=False)
    print(f"\nReport written to {REPORT_FILE}")

    if any(r["Status"] == "FAILED" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
