# Integrated Encryption in Adaptive rANS Compression
### Department of Computer Science — Ariel University

An **adaptive, block-based rANS (range Asymmetric Numeral Systems) entropy
coder** with an integrated encryption mechanism. It applies the scheme of
Klein & Shapira, *"Integrated Encryption in Dynamic Arithmetic Compression"*,
to rANS instead of arithmetic coding.

The core idea: the adaptive model is updated **selectively**, gated by a secret
binary key. At each symbol the model changes only where the key bit is `1`.
Without the correct key, the decoder's model diverges and the output becomes
noise.

---

## How It Works

### The key-gated model (paper, Section 2)

Compression uses an order-0 adaptive frequency model over 256 byte values.
For each processed symbol `i`, two independent actions are gated by the key:

- **Update** — if the next key bit is `1`, increment the symbol's frequency.
- **Swap** — if swaps are enabled and the following key bit is `1`, swap the
  symbol with its neighbor in the interval order (paper, Section 3.4). This
  hides the partition layout, not just the frequencies.

The key is generated from a seed (Mersenne Twister) or supplied directly as a
bit string, and is read circularly.

### Priming (paper, Section 3.2)

Before the real data, the model is warmed up on a fixed, publicly known text
(the opening of *Moby-Dick*). The priming updates are themselves gated by the
secret key, so the model state when the real data begins is already secret.
This closes an attack on the known initial model: without priming, the first
rebuild interval of every block decodes correctly under *any* key. The
`generate_graphs.py` output visualizes this leak (priming on vs. off).

### Two-pass compression

- **Pass 1 (forward)** builds the adaptive model symbol by symbol and saves a
  snapshot every `interval` symbols.
- **Pass 2 (backward)** rANS encodes symbols in reverse (required by rANS),
  rebuilding one interval's table at a time from the snapshots.

The model and key stream run **continuously across blocks**, so a 50 MB file
behaves like one long stream rather than independent 1 MB chunks.

### Decompression (one pass)

The decoder replays the exact same model evolution — same init, same priming,
same key-bit consumption at every step. Any deviation in the key diverges the
model and destroys the output.

### File format (version 2)

```
Header (22 bytes, little-endian):
  [u32] magic  "ARNS"
  [u8 ] version (2)
  [u8 ] flags  (bit0 seed stored, bit1 priming, bit2 swaps)
  [u32] rebuild interval
  [u32] key seed        (0 if not stored)
  [u64] original size
For each 1 MB block:
  [u32] original block size
  [u32] compressed block size
  [bytes] compressed data
```

Storing the interval and the flags in the header means the decoder always uses
the exact settings the encoder used — a mismatch can no longer silently corrupt
the output.

---

## Project Structure

```
ANS-Compression/
├── run_full.py                     master pipeline (all steps below)
│
├── libs/rygrans/                   the compressor (C++17)
│   ├── Config.h                    constants and CodecParams
│   ├── EncryptionKey.{h,cpp}       key from seed or raw bits
│   ├── AdaptiveModel.{h,cpp}       order-0 model + swaps
│   ├── Snapshot.h                  model state snapshot
│   ├── PrimingText.h               public priming text
│   ├── CodecCommon.h               shared header I/O + gated step
│   ├── Compressor.{h,cpp}          two-pass block encoder
│   ├── Decompressor.{h,cpp}        one-pass block decoder
│   ├── main.cpp                    command line tool
│   ├── rans_byte.h                 base rANS (ryg, public domain)
│   ├── run_benchmark.py            build + benchmark on the corpus
│   ├── test_encryption.py          five-scenario encryption suite
│   ├── generate_graphs.py          encryption test graphs
│   └── paper_experiments.py        experiments from paper Section 4
│
├── reference/arith/                arithmetic coding baseline
│   ├── reference_arith_simple/     order-0 arithmetic coder (C)
│   └── compare_algorithms.py       rANS vs. arithmetic comparison
│
├── src/final_summary.py            comparison CSVs + graphs
│
├── files/
│   ├── smallFiles/                 Canterbury corpus
│   └── 50MFiles/                   large (50 MB) files + download_corpus.py
│
└── results/                        generated CSVs and graphs
```

---

## Getting Started

### Prerequisites

- **C/C++ compiler:** GCC/G++ with C++17 (MinGW/TDM-GCC on Windows).
- **Python 3.x** with `pandas`, `matplotlib`, `numpy`:
  ```
  pip install pandas matplotlib numpy
  ```

### The 50 MB dataset

`files/50MFiles/` holds six standard research files from the
[Pizza&Chili Corpus](http://pizzachili.dcc.uchile.cl) (dna, english,
proteins, sources, pitches, dblp.xml), truncated to 50 MB each. They are
currently included in this checkout. If they are ever missing (a fresh
clone that stopped tracking them, or a partial checkout), regenerate them
with:

```
python files/50MFiles/download_corpus.py
```

### Run the full pipeline

```
python run_full.py
```

This builds the compressor and runs every step:

| Step | Script | Output |
|------|--------|--------|
| 1 | `run_benchmark.py` | `results/Rygrans_Results.csv` |
| 2 | `compare_algorithms.py` | `results/Final_Comparison_Report.csv` |
| 3 | `final_summary.py` | comparison CSVs + graphs |
| 4 | `test_encryption.py` | `results/encryption_tests/…` |
| 5 | `generate_graphs.py` | encryption test graphs |
| 6 | `paper_experiments.py` | `results/paper_experiments/…` |

### Use the compressor directly

```
# build
cd libs/rygrans
g++ -O3 -Wall -Wextra main.cpp EncryptionKey.cpp AdaptiveModel.cpp \
    Compressor.cpp Decompressor.cpp -o compressor
```

**Real secret-key mode** — the key is never written to the file; both sides
must already share it, exactly like the paper's threat model:

```
./compressor c input.txt output.rans --seed 42 --no-store-seed
./compressor d output.rans restored.txt --seed 42
```

**Convenience mode (default)** — no key given, so a random seed is chosen
and stored in the file header. The file decrypts itself with no key on the
command line. This is meant for quick testing and benchmarking, not for
demonstrating real secrecy:

```
./compressor c input.txt output.rans
./compressor d output.rans restored.txt
```

Any key can also be given explicitly, with or without storing it:

```
./compressor c input.txt output.rans --seed 42
./compressor d output.rans restored.txt --seed 42
./compressor c input.txt output.rans --key 10110011...
```

Options: `--seed N`, `--key BITS`, `--flip-bit N`, `--interval N`,
`--no-prime`, `--no-swaps`, `--no-store-seed`.
Compression options are recorded in the header; the decoder reads them back.

---

## Encryption Test Suite

`test_encryption.py` runs five scenarios per corpus file:

| Scenario | What it shows |
|----------|---------------|
| Stored seed | file decrypts itself from the header seed → identical |
| Correct key | correct seed passed explicitly → identical |
| Wrong key | with priming, garbage from byte 0 |
| Wrong key, no priming | exposes the first-interval leak priming closes |
| One-bit flip | one differing key bit → correct up to the flip, garbage after |

---

## Paper Experiments (Section 4)

`paper_experiments.py` reproduces the paper's three measurements for rANS:

1. **Compression loss** (Table 1) — random key vs. no key; the loss is a tiny
   number of bytes.
2. **Ciphertext uniformity** (Figure 6, Table 4) — the distribution of every
   *m*-bit substring stays close to `2^-m`; `σ/µ` is reported for `m = 1..8`.
3. **Key sensitivity** (Figure 7) — the normalized Hamming distance between
   ciphertexts under different or one-bit-different keys tends to `0.5`.

---

## Security Notes

This is an academic demonstration of the paper's mechanism, not a production
cipher. Known limitations:

- Deriving the key from a **32-bit seed** gives only a `2^32` key space. Use
  `--key` with a long random bit string for a larger space.
- The key generator is **Mersenne Twister**, which is not cryptographically
  secure. The paper suggests a generator based on the discrete logarithm
  (`K ← aK mod P`, Section 3.1) for stronger key evolution.
- By default the seed is stored in the file header for convenience. Use
  `--no-store-seed` to keep the key fully external.

---

## Technical Details

| Component | Detail |
|-----------|--------|
| Algorithm | byte-aligned rANS |
| Probability scale | 2^14 = 16,384 |
| Block size | 1 MB |
| Default rebuild interval | 512 symbols |
| Key length (from seed) | 1,000 bits, circular |
| Key generator | Mersenne Twister (mt19937) |
| Language | C++17 (engine), Python 3 (pipeline) |
| Base rANS | `rans_byte.h`, Fabian 'ryg' Giesen (public domain) |

---

## Credits

- rANS primitives: [ryg/rans](https://github.com/rygorous/ryg_rans) —
  Fabian Giesen (public domain).
- Arithmetic coding baseline: adapted from Mark Nelson,
  *The Data Compression Book*.
- Scheme: S. T. Klein and D. Shapira, *"Integrated Encryption in Dynamic
  Arithmetic Compression"*, Information and Computation (extended version of
  the LATA 2017 paper).

Developed by Computer Science students at Ariel University.
