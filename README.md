# Integrated rANS Compression & Cryptographic Entropy Analysis

### Department of Computer Science | Ariel University

---

## 📝 Project Overview

This research project explores the intersection of **Entropy Coding** and **Cryptography**. The primary focus is investigating the feasibility and efficiency of compressing data streams that have undergone cryptographic transformations using **Range Asymmetric Numeral Systems (rANS)**.

### The Research Challenge
In information theory, ideal encryption maximizes entropy, making data appear as stochastic noise. According to Shannon's source coding theorem, such data should be incompressible. This project challenges this assumption by evaluating whether specialized rANS implementations can detect and exploit residual redundancies or structural patterns in various encryption-compression pipelines.

## 🎯 Key Objectives

1.  **High-Performance Engine**: Development of a custom C++ implementation of the rANS entropy coder (`Rygrans`).
2.  **Automated Pipeline**: A unified Python-based framework for compilation, execution, and benchmarking.
3.  **Comparative Analysis**: Systematic benchmarking against industry standards (**HTSCodecs**) and theoretical references (**Arithmetic Coding**).

## 📂 System Architecture

The project is organized into modular components separating the core logic, reference models, and analysis tools:

| Directory | Component | Description |
| :--- | :--- | :--- |
| `libs/rygrans` | **Core Engine** | Custom C++ rANS implementation. Optimized for speed and memory efficiency. |
| `libs/htscodecs` | **Reference** | Standard rANS implementation used for validation and benchmarking. |
| `reference/arith` | **Baseline** | Arithmetic coding implementation providing a theoretical compression baseline. |
| `corpus` | **Dataset** | The **Canterbury Corpus**, used as the standard dataset for lossless compression testing. |
| `src` | **Analysis** | Python scripts for statistical aggregation (`final_summary.py`) and diagnostics. |
| `results` | **Output** | Auto-generated CSV reports and visualization graphs. |

## 🚀 Getting Started

### Prerequisites
* **C++ Compiler**: GCC/G++ supporting C++17 or higher (MinGW for Windows / GCC for Linux).
* **Python 3.x**: Required for the automation pipeline.
    * Dependencies: `pandas`, `matplotlib`.

### Installation & Execution

We have developed a **Single-Click Automation Pipeline** (`run_full.py`) that handles the entire research workflow: compilation, testing, verification, and graph generation.

1.  **Clone the Repository**:
    ```bash
    git clone [https://github.com/Matanelevavi/ANS-Compression.git](https://github.com/Matanelevavi/ANS-Compression.git)
    cd ANS-Compression
    ```

2.  **Run the Pipeline**:
    Execute the master script from the root directory:
    ```bash
    python run_full.py
    ```

### Workflow Description
When you run the pipeline, the system automatically performs the following steps:
1.  **Build Rygrans**: Compiles the custom C++ engine and generates compressed artifacts (`.rans` files) for inspection.
2.  **Build HTSCodecs**: Compiles and runs the reference benchmark tool.
3.  **Comparative Benchmark**: Runs the `compare_algorithms.py` script to calculate compression ratios and gaps between the algorithms.
4.  **Final Analysis**: Aggregates all data into a master CSV and generates the performance visualization graph.

## 📊 Benchmarking & Results

Upon completion, all analytical data is stored in the `results/` directory:

### Compression Efficiency Analysis
The graph below illustrates the **Compression Ratio (%)** across different file types (Lower is Better).

![Compression Efficiency Graph](results/comparison_graph.png)

* **`Master_Comparison_Table.csv`**: A unified dataset comparing original sizes, compressed sizes, and ratios across all engines.
* **`comparison_graph.png`**: A visual representation of compression efficiency (Lower Ratio = Better Compression).

### Understanding the Output
* **Rygrans ANS**: Our custom implementation.
* **HTSCodecs**: The industry-standard reference.
* **Arithmetic Ref**: The theoretical baseline.

*The goal is to achieve a compression ratio comparable to or better than the Arithmetic Reference, particularly on high-entropy files.*

## 🛠 Technical Details

* **Language**: C++17 (Engine), Python 3.10+ (Orchestration).
* **Algorithm**: Range Asymmetric Numeral Systems (rANS).
* **Build System**: Custom Python orchestration wrapping GCC commands.

## 📧 Contact & Credits

**Developed by:** Computer Science Students, Ariel University.
