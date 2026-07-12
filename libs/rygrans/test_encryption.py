"""
test_encryption.py - encryption test suite for the adaptive rANS coder.

Five scenarios per corpus file:

  1. Stored seed     decompress with no key given: the seed stored in
                     the file header is used. Expects a perfect copy.
                     (This shows why --no-store-seed exists: a stored
                     seed means the file decrypts itself.)
  2. Correct key     decompress with the correct seed passed
                     explicitly. Expects a perfect copy.
  3. Wrong key       decompress with a different seed. With priming
                     enabled (the default) the output should be
                     garbage from the very first byte.
  4. Wrong key, no priming
                     same, but the file was compressed with
                     --no-prime. This demonstrates the leak that
                     priming closes: the first rebuild interval
                     (512 bytes) decodes correctly under ANY key.
  5. One-bit flip    the encoder key differs from the decoder key in
                     exactly one bit (position FLIP_POS). Compressed
                     with --no-prime --no-swaps --interval 1 so the
                     divergence point is visible: output is correct
                     up to roughly byte FLIP_POS, garbage after.

Results are written to results/encryption_tests/encryption_results.csv.
Restored sample files are kept next to it for inspection (they are
not tracked by git).
"""

import csv
import os
import platform
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

EXE = os.path.join(SCRIPT_DIR,
                   "compressor.exe" if platform.system() == "Windows"
                   else "compressor")

SMALL_FILES_DIR = os.path.join(ROOT_DIR, "files", "smallFiles")
RESULTS_DIR     = os.path.join(ROOT_DIR, "results", "encryption_tests")
LOG_CSV         = os.path.join(RESULTS_DIR, "encryption_results.csv")

# Key bit flipped in the sensitivity scenario.
FLIP_POS = 200

# The one-bit-flip scenario uses --interval 1, which needs a model
# snapshot per symbol. Skip it for files above this size to keep
# memory and runtime reasonable.
FLIP_MAX_FILE_SIZE = 600_000

SCENARIO_STORED     = "Stored seed"
SCENARIO_CORRECT    = "Correct key"
SCENARIO_WRONG      = "Wrong key"
SCENARIO_WRONG_NP   = "Wrong key, no priming"
SCENARIO_FLIP       = f"One-bit flip (pos {FLIP_POS})"


def run_cmd(cmd):
    """Run the compressor; fail loudly if it reports an error."""
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        print(f"  [ERROR] {' '.join(os.path.basename(str(c)) for c in cmd)}")
        print(f"          {stderr}")
        return False
    return True


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def similarity_percent(original, restored):
    if not original or not restored:
        return 0.0
    matches = sum(x == y for x, y in zip(original, restored))
    return 100.0 * matches / max(len(original), len(restored))


def matching_prefix_length(original, restored):
    count = 0
    for x, y in zip(original, restored):
        if x != y:
            break
        count += 1
    return count


def evaluate(label, input_file, rans_path, dec_args, keep_sample=True):
    """Decompress rans_path and compare the result to input_file."""
    original = read_bytes(input_file)
    filename = os.path.basename(input_file)

    restored_path = os.path.join(RESULTS_DIR, "temp_restored.bin")
    if os.path.exists(restored_path):
        os.remove(restored_path)

    if not run_cmd([EXE, "d", rans_path, restored_path] + dec_args):
        return None
    restored = read_bytes(restored_path)

    identical  = (original == restored)
    similarity = similarity_percent(original, restored)
    prefix     = matching_prefix_length(original, restored)

    print(f"  [{label}] identical={'YES' if identical else 'NO'} "
          f"similarity={similarity:.2f}% matching-prefix={prefix}")

    if keep_sample:
        sample_dir = os.path.join(RESULTS_DIR, filename)
        os.makedirs(sample_dir, exist_ok=True)
        sample_name = label.replace(" ", "_").replace(",", "") + "_" + filename
        shutil.copy(restored_path, os.path.join(sample_dir, sample_name))

    os.remove(restored_path)

    return {
        "label":           label,
        "file":            filename,
        "original_size":   len(original),
        "compressed_size": os.path.getsize(rans_path),
        "identical":       identical,
        "similarity":      round(similarity, 4),
        "match_prefix":    prefix,
        "status":          "OK" if identical else "MISMATCH",
    }


def test_file(input_file, results):
    filename = os.path.basename(input_file)
    print(f"\n{'-' * 55}\nFile: {filename}\n{'-' * 55}")

    rans_default = os.path.join(RESULTS_DIR, "temp_default.rans")
    rans_noprime = os.path.join(RESULTS_DIR, "temp_noprime.rans")
    rans_flip    = os.path.join(RESULTS_DIR, "temp_flip.rans")
    seed = 42

    # Compress once with default settings (priming + swaps on).
    if not run_cmd([EXE, "c", input_file, rans_default, "--seed", str(seed)]):
        return

    # 1. Stored seed: no key passed, the header seed is used.
    r = evaluate(SCENARIO_STORED, input_file, rans_default, [])
    if r: results.append(r)

    # 2. Correct key passed explicitly.
    r = evaluate(SCENARIO_CORRECT, input_file, rans_default,
                 ["--seed", str(seed)])
    if r: results.append(r)

    # 3. Wrong key. Priming makes even the first table secret,
    #    so the output should be garbage from byte 0.
    wrong_seed = seed + 12345
    r = evaluate(SCENARIO_WRONG, input_file, rans_default,
                 ["--seed", str(wrong_seed)])
    if r: results.append(r)

    # 4. Wrong key without priming: shows the first-interval leak.
    if run_cmd([EXE, "c", input_file, rans_noprime,
                "--seed", str(seed), "--no-prime"]):
        r = evaluate(SCENARIO_WRONG_NP, input_file, rans_noprime,
                     ["--seed", str(wrong_seed)])
        if r: results.append(r)

    # 5. One-bit flip in the encoder key. Compressed in "ablation"
    #    mode (no priming, no swaps, interval 1) so the divergence
    #    point is exactly at the flipped bit.
    if os.path.getsize(input_file) <= FLIP_MAX_FILE_SIZE:
        if run_cmd([EXE, "c", input_file, rans_flip,
                    "--seed", str(seed), "--flip-bit", str(FLIP_POS),
                    "--no-prime", "--no-swaps", "--interval", "1"]):
            r = evaluate(SCENARIO_FLIP, input_file, rans_flip,
                         ["--seed", str(seed)])
            if r: results.append(r)
    else:
        print(f"  [{SCENARIO_FLIP}] skipped (file too large for interval=1)")

    for p in (rans_default, rans_noprime, rans_flip):
        if os.path.exists(p):
            os.remove(p)


def main():
    if not os.path.exists(EXE):
        print(f"Compressor not found: {EXE}")
        print("Run run_benchmark.py first (it builds the compressor).")
        sys.exit(1)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    test_files = []
    if os.path.isdir(SMALL_FILES_DIR):
        for f in sorted(os.listdir(SMALL_FILES_DIR)):
            path = os.path.join(SMALL_FILES_DIR, f)
            if os.path.isfile(path) and not f.startswith("."):
                test_files.append(path)

    if not test_files:
        print("No test files found.")
        sys.exit(1)

    results = []
    for input_file in test_files:
        test_file(input_file, results)

    with open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "label", "file", "original_size", "compressed_size",
            "identical", "similarity", "match_prefix", "status"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults written to {LOG_CSV}")

    # The suite fails if any "should be identical" scenario mismatched.
    must_match = [r for r in results
                  if r["label"] in (SCENARIO_STORED, SCENARIO_CORRECT)]
    failures = [r for r in must_match if not r["identical"]]
    if failures:
        print(f"FAILURES: {len(failures)} correct-key scenarios mismatched!")
        sys.exit(1)


if __name__ == "__main__":
    main()
