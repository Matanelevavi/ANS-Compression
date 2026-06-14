"""
test_encryption.py — encryption Test Suite for Adaptive Block-rANS
Tests four scenarios:
  1. No key        → compress/decompress without any key
  2. Correct key   → compress/decompress with matching key (seed read from file)
  3. Wrong key     → decompress with completely different key
  4. One-bit flip  → decompress with key differing by exactly one bit at pos 100
"""

import os
import sys
import subprocess
import platform
import struct
import random
import csv
import shutil

# ==========================================
# Configuration
# ==========================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

EXE = os.path.join(SCRIPT_DIR,
                   "compressor.exe" if platform.system() == "Windows"
                   else "compressor")

SMALL_FILES_DIR  = os.path.join(ROOT_DIR, "files", "smallFiles")
RESULTS_DIR = os.path.join(ROOT_DIR, "results", "encryption_tests")
LOG_CSV     = os.path.join(RESULTS_DIR, "encryption_results.csv")

KEY_LENGTH = 1000

os.makedirs(RESULTS_DIR, exist_ok=True)

# ==========================================
# Helpers
# ==========================================

def run_cmd(cmd):
    return subprocess.run(cmd,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()

def mt19937_bits(seed, length):
    """Replicate C++ mt19937 + uniform_int_distribution<int>(0,1)."""
    rng = random.Random(seed)
    return [rng.randint(0, 1) for _ in range(length)]

def read_seed_from_rans(rans_path):
    """Read the 4-byte seed from the .rans file header."""
    with open(rans_path, "rb") as f:
        return struct.unpack("<I", f.read(4))[0]

def bits_to_str(bits):
    return "".join(str(b) for b in bits)

def similarity_percent(a, b):
    if not a or not b:
        return 0.0
    matches = sum(x == y for x, y in zip(a, b))
    return 100.0 * matches / max(len(a), len(b))

def byte_match_prefix(a, b):
    count = 0
    for x, y in zip(a, b):
        if x == y:
            count += 1
        else:
            break
    return count

# ==========================================
# Core Test Runner
# ==========================================

def compress_and_get_seed(input_file, rans_path):
    """Compress input_file and return the seed written to the file."""
    if os.path.exists(rans_path):
        os.remove(rans_path)
    run_cmd([EXE, "c", input_file, rans_path])
    if not os.path.exists(rans_path):
        return None
    return read_seed_from_rans(rans_path)


def decompress_and_evaluate(label, input_file, rans_path, dec_args, keep_files=False):
    """
    Decompress rans_path with dec_args and compare result to input_file.
    Returns a result dict.
    """
    original_data   = read_bytes(input_file)
    filename        = os.path.basename(input_file)
    compressed_size = os.path.getsize(rans_path)
    ratio           = round((compressed_size / len(original_data)) * 100, 2)

    restored_path = os.path.join(RESULTS_DIR, f"temp_{filename}_restored.bin")
    if os.path.exists(restored_path):
        os.remove(restored_path)

    run_cmd([EXE, "d", rans_path, restored_path] + dec_args)

    if not os.path.exists(restored_path):
        print(f"  [{label}] FAILED TO DECOMPRESS")
        return None

    restored_data = read_bytes(restored_path)

    identical    = (original_data == restored_data)
    similarity   = similarity_percent(original_data, restored_data)
    match_prefix = byte_match_prefix(original_data, restored_data)

    print(f"  [{label}]")
    print(f"    Ratio:      {ratio:.2f}%")
    print(f"    Identical:  {'YES' if identical else 'NO'}")
    print(f"    Similarity: {similarity:.2f}%")
    print(f"    Matching bytes from start: {match_prefix}")

    if keep_files:
        file_output_dir = os.path.join(RESULTS_DIR, filename)
        os.makedirs(file_output_dir, exist_ok=True)
        clean_label = label.replace(' ', '_')

        final_path = os.path.join(file_output_dir, f"{clean_label}_{filename}")
        
        shutil.copy(restored_path, final_path)

    if os.path.exists(restored_path):
        os.remove(restored_path)

    return {
        "label":           label,
        "file":            filename,
        "original_size":   len(original_data),
        "compressed_size": compressed_size,
        "ratio":           ratio,
        "identical":       identical,
        "similarity":      similarity,
        "match_prefix":    match_prefix,
        "status":          "OK" if identical else "MISMATCH",
    }

# ==========================================
# Main
# ==========================================

def main():
    test_files = []

    if os.path.exists(SMALL_FILES_DIR):
        for f in sorted(os.listdir(SMALL_FILES_DIR)):
            full_path = os.path.join(SMALL_FILES_DIR, f)
            if os.path.isfile(full_path) and not f.startswith("."):
                test_files.append(full_path)

    if not test_files:
        print("No test files found.")
        sys.exit(1)

    all_results = []

    for input_file in test_files:
        filename = os.path.basename(input_file)
        parent_folder = os.path.basename(os.path.dirname(input_file))

        print(f"\n{'─'*55}")
        print(f"File: {filename}")
        print(f"{'─'*55}")

        rans_path = os.path.join(RESULTS_DIR, f"temp_{filename}.rans")

        # ── Test 1: No key ───────────────────────────────────────
        # Compress (random seed inside), decompress with no args
        # → decompressor reads seed from file and uses it
        seed = compress_and_get_seed(input_file, rans_path)
        if seed is None:
            print("  FAILED TO COMPRESS"); continue

        r = decompress_and_evaluate("No key", input_file, rans_path, [])
        if r: 
            r["folder"] = parent_folder
            all_results.append(r)

        # ── Test 2: Correct key ──────────────────────────────────
        # Compress again (new random seed), then decompress with
        # the SAME seed that was just written to the file
        seed = compress_and_get_seed(input_file, rans_path)
        if seed is None:
            print("  FAILED TO COMPRESS"); continue

        # Pass the correct seed explicitly — must match what's in the file
        r = decompress_and_evaluate(
            "Correct key", input_file, rans_path,
            ["--seed", str(seed)], keep_files=True
        )
        if r: 
            r["folder"] = parent_folder
            all_results.append(r)

        # ── Test 3: Wrong key ────────────────────────────────────
        # Reuse same .rans file, decompress with a different seed
        wrong_seed = (seed + 12345) % (2**32)
        r = decompress_and_evaluate(
            "Wrong key", input_file, rans_path,
            ["--seed", str(wrong_seed), "--interval", "1"], keep_files=True
        )
        if r: 
            r["folder"] = parent_folder
            all_results.append(r)

        # ── Test 4: One-bit flip at position 100 ─────────────────
        # Build the correct key, flip exactly one bit, pass as --key
        rans_path_flip = os.path.join(RESULTS_DIR, f"temp_{filename}.flip.rans")
        run_cmd([EXE, "c", input_file, rans_path_flip, "--seed", str(seed), "--flip-bit", "100", "--interval", "1"])
        
        # 2. מפענחים באמצעות ה-Seed המקורי והנקי! (חוסר התיאום בביט 100 יגרום לקריסה)
        r = decompress_and_evaluate(
            "One-bit flip (pos 100)", input_file, rans_path_flip,
            ["--seed", str(seed), "--interval", "1"], keep_files=True
        )
        if r: 
            r["folder"] = parent_folder
            all_results.append(r)

        # Cleanup
        if os.path.exists(rans_path):
            os.remove(rans_path)
            
        rans_path_flip = os.path.join(RESULTS_DIR, f"temp_{filename}.flip.rans")
        if os.path.exists(rans_path_flip):
            os.remove(rans_path_flip)

   # ── Save Comprehensive CSV ───────────────────────────────────
    with open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "folder", "label", "file", "original_size", "compressed_size",
            "ratio", "identical", "similarity", "match_prefix", "status"
        ])
        writer.writeheader()
        writer.writerows(all_results)



if __name__ == "__main__":
    main()