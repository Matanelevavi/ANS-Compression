# Adaptive rANS with Integrated Encryption Key
### Department of Computer Science — Ariel University

---

## Overview

This project implements an **adaptive, block-based rANS (Range Asymmetric Numeral Systems) entropy coder** with an integrated encryption mechanism. The core idea, derived from the paper *"Integrated Encryption in Dynamic Arithmetic Compression"*, is to condition model updates on a binary encryption key: at each symbol, the adaptive model updates only if the corresponding key bit is `1`. Without the key, decompression produces completely different output.

The project benchmarks this custom engine against two reference implementations — **HTSCodecs** (industry-standard rANS) and a classic **Arithmetic Coding** baseline — and validates the encryption behavior through a dedicated test suite.

---

## How It Works

### Compression (Two-Pass)

**Pass 1 (forward):** The encoder scans the input and builds an adaptive probability model symbol by symbol. At each symbol, it queries the encryption key:
- Key bit = `1` → model updates (learns the symbol's frequency)
- Key bit = `0` → model does not update (encryption step)

A snapshot of the model state is saved every `REBUILD_INTERVAL = 512` symbols.

**Pass 2 (backward):** rANS encodes symbols in reverse order (required by the algorithm). Each symbol is encoded using the probability table built from its interval's snapshot.

### Decompression (One Pass)

The decoder replicates the encoder's model evolution exactly — same initialization, same key, same update condition at every symbol. Any deviation in the key causes the model to diverge immediately, producing garbled output.

### File Format

```
[uint32] seed              ← 4 bytes; used to reconstruct the key
[uint32] total_size        ← original file size
for each 1MB block:
  [uint32] original_block_size
  [uint32] compressed_block_size
  [bytes]  compressed data
```

---

## Project Structure

```
ANS-Compression/
├── run_full.py                        ← master pipeline script
│
├── libs/
│   ├── rygrans/                       ← custom rANS engine (C++)
│   │   ├── Config.h                   ← constants: PROB_BITS, BLOCK_SIZE, REBUILD_INTERVAL
│   │   ├── Snapshot.h                 ← model state snapshot struct
│   │   ├── EncryptionKey.h/.cpp       ← key management (seed / raw bits)
│   │   ├── AdaptiveModel.h/.cpp       ← adaptive probability model
│   │   ├── Compressor.h/.cpp          ← two-pass block encoder
│   │   ├── Decompressor.h/.cpp        ← forward-pass block decoder
│   │   ├── main.cpp                   ← CLI entry point
│   │   ├── run_benchmark.py           ← compile + benchmark on corpus
│   │   ├── test_encryption.py         ← 4-scenario encryption test suite
│   │   └── generate_graphs.py         ← visualization from test results
│   │
│   └── htscodecs/                     ← reference rANS (HTSCodecs)
│
├── reference/arith/                   ← arithmetic coding baseline
│   └── compare_algorithms.py          ← benchmark all three engines
│
├── files/
│   ├── smallFiles/                    ← Canterbury corpus (small files)
│   └── 50MFiles/                      ← large file dataset (50MB each)
│
├── src/
│   └── final_summary.py               ← aggregate results + comparison graphs
│
└── results/                           ← auto-generated output
    ├── ADAPRANS_Results.csv
    ├── HTSCodecs_Results.csv
    ├── Final_Comparison_Report.csv
    ├── comparison_graph_small.png
    ├── comparison_graph_large.png
    └── encryption_tests/
        ├── encryption_results.csv
        ├── graph1_similarity.png
        ├── graph2_prefix.png
        ├── graph3_ratio.png
        └── graph4_heatmap.png
```

---

## Getting Started

### Prerequisites

- **C++ compiler:** GCC/G++ with C++17 support (MinGW on Windows, GCC on Linux/macOS)
- **Python 3.x** with: `pandas`, `matplotlib`, `seaborn`

Install Python dependencies:
```bash
pip install pandas matplotlib seaborn
```

### Run the Full Pipeline

```bash
python run_full.py
```

This single command executes all five steps in order:

| Step | Script | Output |
|------|--------|--------|
| 1 | `run_benchmark.py` | `ADAPRANS_Results.csv` |
| 2 | `compare_algorithms.py` | `Final_Comparison_Report.csv` |
| 3 | `final_summary.py` | comparison graphs |
| 4 | `test_encryption.py` | `encryption_results.csv` + restored files |
| 5 | `generate_graphs.py` | encryption test graphs |

### Run Individual Steps

```bash
# Benchmark only
cd libs/rygrans
python run_benchmark.py

# Encryption tests only
cd libs/rygrans
python test_encryption.py

# Compress / decompress manually
./compressor.exe c input.txt output.rans
./compressor.exe d output.rans restored.txt
./compressor.exe d output.rans restored.txt --seed 42
./compressor.exe d output.rans restored.txt --key 1011001101...
```

---

## Encryption Test Suite

`test_encryption.py` runs four scenarios on each file in the corpus:

| Scenario | Key Used | Expected Result |
|----------|----------|-----------------|
| No key | none (model always updates) | 100% identical |
| Correct key | seed read from compressed file | 100% identical |
| Wrong key | different seed | ~0.5% similarity — immediate gibberish |
| One-bit flip (pos 100) | correct key with bit 100 flipped | correct up to ~byte 100, gibberish after |

### Sample Results

| File | No key | Correct key | Wrong key | One-bit flip |
|------|--------|-------------|-----------|--------------|
| alice29.txt | 100% | 100% | 0.49% | 2.80% (102 bytes) |
| asyoulik.txt | 100% | 100% | 0.56% | 1.54% (103 bytes) |
| kennedy.xls | 100% | 100% | 0.00% | 0.00% |

The one-bit flip result confirms that the encryption is **sensitive to individual bit errors**: the output is correct up to the point where the key diverges, then immediately becomes unrecoverable.

---

## Compression Results

Benchmarked on the Canterbury corpus. Compression ratio = compressed size / original size (lower is better).

| Engine | Type | Avg. Ratio (small files) |
|--------|------|--------------------------|
| Rygrans (this project) | Adaptive rANS + encryption | ~57–70% |
| HTSCodecs | Standard rANS | ~57–70% |
| Arithmetic Coding | Order-0 adaptive | ~57–70% |

All three engines achieve comparable compression ratios, confirming that the encryption key mechanism does **not degrade compression performance**.

---

## Technical Details

| Component | Detail |
|-----------|--------|
| Algorithm | Range Asymmetric Numeral Systems (rANS), byte-aligned |
| Probability scale | 2^14 = 16,384 |
| Block size | 1 MB |
| Table rebuild interval | every 512 symbols |
| Key length | 1,000 bits (circular) |
| Key generation | Mersenne Twister (mt19937) seeded with `std::random_device` |
| Language | C++17 (engine), Python 3.10+ (pipeline) |
| Base rANS implementation | `rans_byte.h` by Fabian 'ryg' Giesen (public domain) |

---

## Credits

Developed by Computer Science students at Ariel University.  
Based on the paper: *"Integrated Encryption in Dynamic Arithmetic Compression"*.  
Base rANS primitives: [ryg/rans](https://github.com/rygorous/ryg_rans) — Fabian Giesen (public domain).
