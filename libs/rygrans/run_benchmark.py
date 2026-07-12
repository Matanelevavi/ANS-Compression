"""
run_benchmark.py - compile the compressor and benchmark it.

For every file in the two datasets (smallFiles and 50MFiles) this
script measures compression ratio, compression time, decompression
time, and verifies that the decompressed file is bit-identical to
the original. Results are written to results/Rygrans_Results.csv.
"""

import csv
import os
import platform
import subprocess
import sys
import tempfile
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

EXE_NAME = "compressor.exe" if platform.system() == "Windows" else "compressor"
EXE_PATH = os.path.join(SCRIPT_DIR, EXE_NAME)

DATASET_SMALL = os.path.join(ROOT_DIR, "files", "smallFiles")
DATASET_LARGE = os.path.join(ROOT_DIR, "files", "50MFiles")
LOG_CSV       = os.path.join(ROOT_DIR, "results", "Rygrans_Results.csv")

SOURCES = [
    "main.cpp",
    "EncryptionKey.cpp",
    "AdaptiveModel.cpp",
    "Compressor.cpp",
    "Decompressor.cpp",
]


def build():
    """Compile the compressor with optimizations and all warnings."""
    sources = [os.path.join(SCRIPT_DIR, s) for s in SOURCES]
    cmd = ["g++", "-O3", "-Wall", "-Wextra"] + sources + ["-o", EXE_PATH]
    print("Building compressor...")
    result = subprocess.run(cmd, stderr=subprocess.PIPE)
    stderr = result.stderr.decode(errors="replace").strip()
    if stderr:
        print(stderr)
    if result.returncode != 0:
        print("Build failed.")
        sys.exit(1)
    print("Build OK.")


def files_identical(path_a, path_b):
    """Compare two files byte by byte without loading both fully."""
    if os.path.getsize(path_a) != os.path.getsize(path_b):
        return False
    with open(path_a, "rb") as fa, open(path_b, "rb") as fb:
        while True:
            chunk_a = fa.read(1 << 20)
            chunk_b = fb.read(1 << 20)
            if chunk_a != chunk_b:
                return False
            if not chunk_a:
                return True


def run_dataset(dataset_path, dataset_name, writer, temp_dir):
    """Benchmark every file in one dataset directory."""
    if not os.path.isdir(dataset_path):
        print(f"  [Warning] dataset not found: {dataset_path}")
        return

    for filename in sorted(os.listdir(dataset_path)):
        file_path = os.path.join(dataset_path, filename)
        if not os.path.isfile(file_path) or filename.startswith("."):
            continue

        original_size = os.path.getsize(file_path)
        comp_path     = os.path.join(temp_dir, filename + ".rans")
        restored_path = os.path.join(temp_dir, filename + ".restored")

        try:
            start = time.perf_counter()
            subprocess.run([EXE_PATH, "c", file_path, comp_path],
                           stdout=subprocess.DEVNULL, check=True)
            comp_time = round((time.perf_counter() - start) * 1000, 2)
            compressed_size = os.path.getsize(comp_path)

            start = time.perf_counter()
            subprocess.run([EXE_PATH, "d", comp_path, restored_path],
                           stdout=subprocess.DEVNULL, check=True)
            decomp_time = round((time.perf_counter() - start) * 1000, 2)

            if files_identical(file_path, restored_path):
                ratio   = round(compressed_size / original_size * 100, 2) if original_size else 0.0
                savings = round(100 - ratio, 2) if original_size else 0.0
                status  = "SUCCESS"
                print(f"  OK   {filename}: ratio {ratio}%")
            else:
                ratio = savings = comp_time = decomp_time = 0.0
                status = "INTEGRITY ERROR"
                print(f"  FAIL {filename}: decompressed output differs!")

            writer.writerow([dataset_name, filename, original_size,
                             compressed_size, ratio, savings,
                             comp_time, decomp_time, status])

        except subprocess.CalledProcessError as e:
            print(f"  FAIL {filename}: compressor exited with code {e.returncode}")
            writer.writerow([dataset_name, filename, original_size,
                             0, 0.0, 0.0, 0.0, 0.0, "RUNTIME ERROR"])
        finally:
            for p in (comp_path, restored_path):
                if os.path.exists(p):
                    os.remove(p)


def main():
    build()
    os.makedirs(os.path.dirname(LOG_CSV), exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="rygrans_bench_") as temp_dir, \
         open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Dataset", "Filename", "Original_Size",
                         "Compressed_Size", "Ratio_Percent", "Savings_Percent",
                         "Comp_Time_MS", "Decomp_Time_MS", "Status"])

        print("\nBenchmarking small files...")
        run_dataset(DATASET_SMALL, "smallFiles", writer, temp_dir)

        print("\nBenchmarking 50MB files...")
        run_dataset(DATASET_LARGE, "50MFiles", writer, temp_dir)

    print(f"\nResults written to {LOG_CSV}")


if __name__ == "__main__":
    main()
