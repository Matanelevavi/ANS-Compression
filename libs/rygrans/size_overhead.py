"""
size_overhead.py - does encryption cost any extra bytes?

Compresses every corpus file twice with the same secret key:

  1. "demo" mode    default settings, the key seed is stored in the
                    header (self-decrypting, for convenience)
  2. "secret" mode  --no-store-seed: the seed is left out, the key
                    must be supplied separately to decompress

Because encryption in this scheme is integrated into the adaptive
model updates (not a cipher bolted on afterwards), the two modes
produce byte-identical output. This script measures that directly
instead of assuming it, and plots original vs. compressed vs.
compressed-and-secret size per file.

Reads   files/smallFiles/*, files/50MFiles/*
Writes  results/Size_Overhead.csv,
        results/size_overhead_small.png,
        results/size_overhead_large.png
"""

import csv
import os
import platform
import subprocess
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

EXE_NAME = "compressor.exe" if platform.system() == "Windows" else "compressor"
EXE_PATH = os.path.join(SCRIPT_DIR, EXE_NAME)

DATASETS = [
    ("smallFiles", os.path.join(ROOT_DIR, "files", "smallFiles")),
    ("50MFiles",   os.path.join(ROOT_DIR, "files", "50MFiles")),
]

RESULTS_DIR = os.path.join(ROOT_DIR, "results")
CSV_PATH    = os.path.join(RESULTS_DIR, "Size_Overhead.csv")

SEED = 42

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.grid": True,
    "axes.axisbelow": True,
})


def compress(input_path, output_path, extra_args):
    cmd = [EXE_PATH, "c", input_path, output_path,
           "--seed", str(SEED)] + extra_args
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        print(f"  [ERROR] {os.path.basename(input_path)}: {stderr}")
        return None
    return os.path.getsize(output_path)


def measure_dataset(name, path, temp_dir):
    rows = []
    if not os.path.isdir(path):
        print(f"  [Warning] dataset not found: {path}")
        return rows

    for filename in sorted(os.listdir(path)):
        file_path = os.path.join(path, filename)
        if not os.path.isfile(file_path) or filename.startswith("."):
            continue
        if filename.endswith(".py"):
            continue  # tooling script, not corpus data

        original_size = os.path.getsize(file_path)
        demo_path   = os.path.join(temp_dir, filename + ".demo.rans")
        secret_path = os.path.join(temp_dir, filename + ".secret.rans")

        print(f"  {filename} ({original_size:,} B)...")
        demo_size   = compress(file_path, demo_path, [])
        secret_size = compress(file_path, secret_path, ["--no-store-seed"])
        if demo_size is None or secret_size is None:
            continue

        rows.append({
            "Dataset": name,
            "File Name": filename,
            "Original Size (B)": original_size,
            "ANS Compressed Size (B)": demo_size,
            "ANS Compressed + Secret Key Size (B)": secret_size,
        })

        for p in (demo_path, secret_path):
            if os.path.exists(p):
                os.remove(p)

    return rows


def save_csv(rows):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Dataset", "File Name", "Original Size (B)",
            "ANS Compressed Size (B)",
            "ANS Compressed + Secret Key Size (B)"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV written: {CSV_PATH}")


def plot_dataset(rows, dataset_name, output_path, title):
    subset = [r for r in rows if r["Dataset"] == dataset_name]
    if not subset:
        print(f"Skipping graph '{output_path}': no data.")
        return

    names      = [r["File Name"] for r in subset]
    original   = [r["Original Size (B)"] for r in subset]
    compressed = [r["ANS Compressed Size (B)"] for r in subset]
    secret     = [r["ANS Compressed + Secret Key Size (B)"] for r in subset]

    x = np.arange(len(names))
    width = 0.27

    fig, ax = plt.subplots(figsize=(max(9, len(names) * 1.1), 6))
    ax.bar(x - width, original, width, label="Original", color="#9E9E9E")
    ax.bar(x, compressed, width, label="ANS compressed", color="#2196F3")
    ax.bar(x + width, secret, width,
           label="ANS compressed + secret key", color="#4CAF50")

    ax.set_ylabel("File size in bytes")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=35, ha="right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Graph created: {output_path}")


def main():
    if not os.path.exists(EXE_PATH):
        print(f"Compressor not found: {EXE_PATH}")
        print("Run run_benchmark.py first (it builds the compressor).")
        sys.exit(1)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for name, path in DATASETS:
            print(f"\nDataset: {name}")
            rows.extend(measure_dataset(name, path, temp_dir))

    save_csv(rows)
    plot_dataset(rows, "smallFiles",
                 os.path.join(RESULTS_DIR, "size_overhead_small.png"),
                 "Original vs. Compressed vs. Compressed+Encrypted"
                 " - Small Files (Canterbury corpus)")
    plot_dataset(rows, "50MFiles",
                 os.path.join(RESULTS_DIR, "size_overhead_large.png"),
                 "Original vs. Compressed vs. Compressed+Encrypted"
                 " - Large Files (50 MB)")


if __name__ == "__main__":
    main()
