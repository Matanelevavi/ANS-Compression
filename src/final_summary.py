"""
final_summary.py - split the comparison report per dataset and
draw the compression ratio graphs.

Reads  results/Final_Comparison_Report.csv
Writes results/Comparison_Small.csv, results/Comparison_Large.csv,
       results/comparison_graph_small.png,
       results/comparison_graph_large.png
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
RESULTS    = os.path.join(ROOT_DIR, "results")

REPORT_FILE = os.path.join(RESULTS, "Final_Comparison_Report.csv")

OUTPUT_SMALL       = os.path.join(RESULTS, "Comparison_Small.csv")
OUTPUT_LARGE       = os.path.join(RESULTS, "Comparison_Large.csv")
OUTPUT_GRAPH_SMALL = os.path.join(RESULTS, "comparison_graph_small.png")
OUTPUT_GRAPH_LARGE = os.path.join(RESULTS, "comparison_graph_large.png")


def save_graph(df, output_path, title):
    if df.empty:
        print(f"Skipping graph '{output_path}': no data.")
        return

    x = np.arange(len(df))
    width = 0.35

    plt.figure(figsize=(14, 7))
    plt.bar(x - width / 2, df["Rygrans Ratio (%)"], width=width,
            label="Rygrans (adaptive rANS + encryption)")
    plt.bar(x + width / 2, df["Arithmetic Ratio (%)"], width=width,
            label="Arithmetic coding (order-0 baseline)")
    plt.xticks(x, df["File Name"], rotation=45, ha="right")
    plt.ylabel("Compression ratio % (lower is better)")
    plt.title(title)
    plt.grid(axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Graph created: {output_path}")


def main():
    if not os.path.exists(REPORT_FILE):
        print(f"Missing report: {REPORT_FILE}")
        print("Run reference/arith/compare_algorithms.py first.")
        sys.exit(1)

    df = pd.read_csv(REPORT_FILE)
    df.columns = df.columns.str.strip()

    if "Status" in df.columns:
        df = df[df["Status"] == "OK"]

    small_df = df[df["Dataset"] == "smallFiles"].copy()
    large_df = df[df["Dataset"] == "50MFiles"].copy()

    small_df.to_csv(OUTPUT_SMALL, index=False)
    large_df.to_csv(OUTPUT_LARGE, index=False)

    save_graph(small_df, OUTPUT_GRAPH_SMALL,
               "Compression Comparison - Small Files (Canterbury corpus)")
    save_graph(large_df, OUTPUT_GRAPH_LARGE,
               "Compression Comparison - Large Files (50 MB)")


if __name__ == "__main__":
    main()
