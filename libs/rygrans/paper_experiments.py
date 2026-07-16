"""
paper_experiments.py - the three experiments from Section 4 of
Klein & Shapira, "Integrated Encryption in Dynamic Arithmetic
Compression", reproduced here for the rANS variant.

  Experiment 1 (paper Table 1): compression loss.
      Compare the compressed size with a random secret key against
      the size with no key (model updated at every step). The paper
      reports a negligible loss; we expect the same.

  Experiment 2 (paper Figure 6 + Table 4): ciphertext uniformity.
      A well-encrypted stream should look random: every m-bit
      substring should appear with probability 2^-m. We measure the
      distribution over all bit offsets and report sigma/mu.

  Experiment 3 (paper Figure 7): key sensitivity.
      The normalized Hamming distance between ciphertexts produced
      with two different keys, or keys differing in a single bit,
      should tend to 0.5 (completely unrelated bitstreams).

Both isolated variants use --no-prime --no-swaps so that the ONLY
difference between "no key" and "random key" is the selective
update rule, exactly like in the paper.

Outputs are written to results/paper_experiments/.
"""

import os
import platform
import struct
import subprocess
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

EXE = os.path.join(SCRIPT_DIR,
                   "compressor.exe" if platform.system() == "Windows"
                   else "compressor")

SMALL_DIR = os.path.join(ROOT_DIR, "files", "smallFiles")
LARGE_DIR = os.path.join(ROOT_DIR, "files", "50MFiles")
OUT_DIR   = os.path.join(ROOT_DIR, "results", "paper_experiments")

HEADER_SIZE = 22  # magic(4) version(1) flags(1) interval(4) seed(4) size(8)

# File used for the uniformity and sensitivity experiments
# (the paper uses one representative text file, ebib).
PROBE_FILE = os.path.join(SMALL_DIR, "lcet10.txt")

# Limit for the bit-level analysis, for speed.
MAX_ANALYZED_BYTES = 4 * 1024 * 1024

SEED_A = 42
SEED_B = 777


def run_compressor(args):
    result = subprocess.run([EXE] + args, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stderr.decode(errors="replace"))
        sys.exit(1)


def compressed_payload(rans_path):
    """Concatenate the compressed block payloads (headers stripped)."""
    payload = bytearray()
    with open(rans_path, "rb") as f:
        f.seek(HEADER_SIZE)
        while True:
            block_header = f.read(8)
            if len(block_header) < 8:
                break
            _, comp_size = struct.unpack("<II", block_header)
            payload += f.read(comp_size)
    return bytes(payload)


# ----------------------------------------------------------------
# Experiment 1: compression loss (paper Table 1)
# ----------------------------------------------------------------

def experiment_compression_loss(temp_dir):
    print("\nExperiment 1: compression loss (key vs no key)")

    rows = []
    datasets = [("smallFiles", SMALL_DIR), ("50MFiles", LARGE_DIR)]
    for dataset_name, dataset_dir in datasets:
        if not os.path.isdir(dataset_dir):
            continue
        for filename in sorted(os.listdir(dataset_dir)):
            path = os.path.join(dataset_dir, filename)
            if not os.path.isfile(path) or filename.endswith(".py"):
                continue

            out_nokey = os.path.join(temp_dir, "nokey.rans")
            out_key   = os.path.join(temp_dir, "key.rans")

            # "No key": a one-bit key of 1 updates the model at
            # every step, like standard adaptive coding.
            run_compressor(["c", path, out_nokey, "--key", "1",
                            "--no-prime", "--no-swaps"])
            run_compressor(["c", path, out_key, "--seed", str(SEED_A),
                            "--no-prime", "--no-swaps"])

            size_nokey = os.path.getsize(out_nokey)
            size_key   = os.path.getsize(out_key)
            loss       = size_key - size_nokey
            orig       = os.path.getsize(path)

            rows.append({
                "Dataset": dataset_name,
                "File": filename,
                "Original (B)": orig,
                "No key (B)": size_nokey,
                "Random key (B)": size_key,
                "Absolute loss (B)": loss,
                "Relative loss": round(loss / orig, 9) if orig else 0.0,
            })
            print(f"  {filename:<22} no-key={size_nokey:>10}  "
                  f"key={size_key:>10}  loss={loss:>+6} bytes")

            os.remove(out_nokey)
            os.remove(out_key)

    df = pd.DataFrame(rows)
    out_csv = os.path.join(OUT_DIR, "table1_compression_loss.csv")
    df.to_csv(out_csv, index=False)
    print(f"  -> {out_csv}")


# ----------------------------------------------------------------
# Experiment 2: ciphertext uniformity (paper Figure 6 / Table 4)
# ----------------------------------------------------------------

def mbit_distribution(payload, m):
    """Probability of every m-bit value over all bit offsets."""
    data = payload[:MAX_ANALYZED_BYTES]
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    n = len(bits) - m + 1
    values = np.zeros(n, dtype=np.uint32)
    for j in range(m):
        values += bits[j:j + n].astype(np.uint32) << (m - 1 - j)
    counts = np.bincount(values, minlength=1 << m)
    return counts / counts.sum()


def experiment_uniformity(temp_dir):
    print("\nExperiment 2: ciphertext uniformity")

    out_std = os.path.join(temp_dir, "std.rans")
    out_sel = os.path.join(temp_dir, "sel.rans")
    run_compressor(["c", PROBE_FILE, out_std, "--key", "1",
                    "--no-prime", "--no-swaps"])
    run_compressor(["c", PROBE_FILE, out_sel, "--seed", str(SEED_A),
                    "--no-prime", "--no-swaps"])

    payload_std = compressed_payload(out_std)
    payload_sel = compressed_payload(out_sel)

    # sigma/mu ratio per m, for both variants (paper Table 4).
    rows = []
    for m in range(1, 9):
        p_std = mbit_distribution(payload_std, m)
        p_sel = mbit_distribution(payload_sel, m)
        rows.append({
            "m": m,
            "sigma/mu (no key)": round(p_std.std() / p_std.mean(), 6),
            "sigma/mu (random key)": round(p_sel.std() / p_sel.mean(), 6),
        })
    df = pd.DataFrame(rows)
    out_csv = os.path.join(OUT_DIR, "table4_sigma_mu.csv")
    df.to_csv(out_csv, index=False)
    print(df.to_string(index=False))
    print(f"  -> {out_csv}")

    # 8-bit distribution plot (paper Figure 6, left side).
    p_std = mbit_distribution(payload_std, 8)
    p_sel = mbit_distribution(payload_sel, 8)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(p_sel, label="With random key", linewidth=1.0)
    ax.plot(p_std, label="No key", linewidth=1.0, alpha=0.7)
    ax.axhline(1 / 256, linestyle="--", color="black", alpha=0.6,
               label="Uniform (1/256)")
    ax.set_xlabel("8-bit value")
    ax.set_ylabel("Probability of occurrence")
    ax.set_title("Distribution of 8-bit Substrings in the Compressed Stream")
    ax.set_ylim(0, 2 / 256)  # symmetric around the uniform line, centered
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(os.path.join(OUT_DIR, "figure6_uniformity_8bit.png"),
                dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  -> figure6_uniformity_8bit.png")

    os.remove(out_std)
    os.remove(out_sel)


# ----------------------------------------------------------------
# Experiment 3: key sensitivity (paper Figure 7)
# ----------------------------------------------------------------

def hamming_curve(payload_a, payload_b):
    """Cumulative normalized Hamming distance between two streams."""
    n = min(len(payload_a), len(payload_b), MAX_ANALYZED_BYTES)
    bits_a = np.unpackbits(np.frombuffer(payload_a[:n], dtype=np.uint8))
    bits_b = np.unpackbits(np.frombuffer(payload_b[:n], dtype=np.uint8))
    diff = (bits_a ^ bits_b).astype(np.float64)
    cum = np.cumsum(diff) / np.arange(1, len(diff) + 1)
    return cum


def experiment_sensitivity(temp_dir):
    print("\nExperiment 3: key sensitivity (normalized Hamming distance)")

    variants = {
        "reference (seed A)":      ["--seed", str(SEED_A)],
        "different key (seed B)":  ["--seed", str(SEED_B)],
        "first key bit flipped":   ["--seed", str(SEED_A), "--flip-bit", "0"],
        "last key bit flipped":    ["--seed", str(SEED_A), "--flip-bit", "999"],
    }

    payloads = {}
    for name, key_args in variants.items():
        out = os.path.join(temp_dir, "sens.rans")
        run_compressor(["c", PROBE_FILE, out] + key_args +
                       ["--no-prime", "--no-swaps"])
        payloads[name] = compressed_payload(out)
        os.remove(out)

    reference = payloads.pop("reference (seed A)")

    fig, ax = plt.subplots(figsize=(10, 5))
    rows = []
    for name, payload in payloads.items():
        curve = hamming_curve(reference, payload)
        ax.plot(np.arange(1, len(curve) + 1) / 8.0, curve,
                label=name, linewidth=1.2)
        rows.append({"variant": name,
                     "final normalized Hamming distance":
                         round(float(curve[-1]), 6)})
        print(f"  vs {name:<24} -> {curve[-1]:.6f}")

    ax.axhline(0.5, linestyle="--", color="black", alpha=0.6,
               label="Expected value 0.5")
    ax.set_xscale("log")
    ax.set_xlabel("Compressed bytes compared")
    ax.set_ylabel("Normalized Hamming distance")
    ax.set_ylim(0, 1)
    ax.set_title("Ciphertext Sensitivity to Key Changes")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)
    fig.savefig(os.path.join(OUT_DIR, "figure7_hamming_distance.png"),
                dpi=300, bbox_inches="tight")
    plt.close(fig)

    out_csv = os.path.join(OUT_DIR, "figure7_final_values.csv")
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print("  -> figure7_hamming_distance.png")


def main():
    if not os.path.exists(EXE):
        print(f"Compressor not found: {EXE}")
        print("Run run_benchmark.py first (it builds the compressor).")
        sys.exit(1)
    if not os.path.exists(PROBE_FILE):
        print(f"Probe file not found: {PROBE_FILE}")
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ans_paper_") as temp_dir:
        experiment_compression_loss(temp_dir)
        experiment_uniformity(temp_dir)
        experiment_sensitivity(temp_dir)

    print("\nPaper experiments done.")


if __name__ == "__main__":
    main()
