"""
generate_graphs.py - visualization of the encryption test results.

Reads results/encryption_tests/encryption_results.csv (produced by
test_encryption.py) and creates four graphs in the same directory:

  graph1_similarity.png     average similarity per scenario
  graph2_failure_distance.png  matching prefix before divergence
  graph3_leak_comparison.png   priming ON vs OFF under a wrong key
  graph4_heatmap.png        similarity per file and scenario
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

RESULTS_DIR = os.path.join(ROOT_DIR, "results", "encryption_tests")
CSV_PATH    = os.path.join(RESULTS_DIR, "encryption_results.csv")

FLIP_POS = 200  # must match test_encryption.py

LABEL_STORED   = "Stored seed"
LABEL_CORRECT  = "Correct key"
LABEL_WRONG    = "Wrong key"
LABEL_WRONG_NP = "Wrong key, no priming"
LABEL_FLIP     = f"One-bit flip (pos {FLIP_POS})"

LABEL_ORDER = [LABEL_STORED, LABEL_CORRECT, LABEL_WRONG,
               LABEL_WRONG_NP, LABEL_FLIP]

PALETTE = {
    LABEL_STORED:   "#2196F3",
    LABEL_CORRECT:  "#4CAF50",
    LABEL_WRONG:    "#F44336",
    LABEL_WRONG_NP: "#9C27B0",
    LABEL_FLIP:     "#FF9800",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.grid": True,
    "axes.axisbelow": True,
})


def load_data():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        print("Run test_encryption.py first.")
        sys.exit(1)
    df = pd.read_csv(CSV_PATH)
    df["label"] = pd.Categorical(df["label"], categories=LABEL_ORDER,
                                 ordered=True)
    return df


def save(fig, name):
    path = os.path.join(RESULTS_DIR, name)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {name}")


def graph_similarity(df):
    """Average similarity to the original file, per scenario."""
    agg = (df.groupby("label", observed=True)["similarity"]
             .mean().reindex(LABEL_ORDER).dropna())

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [PALETTE[x] for x in agg.index]
    bars = ax.bar(agg.index, agg.values, color=colors)
    for b, v in zip(bars, agg.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%",
                ha="center", fontweight="bold")
    ax.set_ylim(0, 112)
    ax.set_ylabel("Similarity to original (%)")
    ax.set_title("Average Similarity per Scenario")
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    save(fig, "graph1_similarity.png")


def graph_failure_distance(df):
    """How many bytes match before the output diverges."""
    scenarios = [LABEL_WRONG, LABEL_WRONG_NP, LABEL_FLIP]
    err = df[df["label"].isin(scenarios)]

    fig, ax = plt.subplots(figsize=(9, 5))
    for x, label in enumerate(scenarios):
        subset = err[err["label"] == label]
        if subset.empty:
            continue
        jitter = np.random.default_rng(0).normal(x, 0.04, len(subset))
        ax.scatter(jitter, subset["match_prefix"], s=60,
                   color=PALETTE[label], alpha=0.85, label=label)

    ax.axhline(512, linestyle="--", color="gray", alpha=0.8,
               label="Rebuild interval (512)")
    ax.axhline(FLIP_POS, linestyle=":", color="black", alpha=0.8,
               label=f"Flipped bit ({FLIP_POS})")
    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels(scenarios, rotation=10, ha="right")
    ax.set_ylabel("Matching prefix length (bytes)")
    ax.set_yscale("symlog")
    ax.set_title("Failure Distance Before Divergence")
    ax.legend()
    save(fig, "graph2_failure_distance.png")


def graph_leak_comparison(df):
    """Priming ON vs OFF under a wrong key, per file."""
    wrong    = df[df["label"] == LABEL_WRONG].set_index("file")
    wrong_np = df[df["label"] == LABEL_WRONG_NP].set_index("file")
    files = sorted(set(wrong.index) & set(wrong_np.index))
    if not files:
        return

    x = np.arange(len(files))
    width = 0.38

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - width / 2, [wrong_np.loc[f, "match_prefix"] for f in files],
           width, color=PALETTE[LABEL_WRONG_NP], label="No priming")
    ax.bar(x + width / 2, [wrong.loc[f, "match_prefix"] for f in files],
           width, color=PALETTE[LABEL_WRONG], label="With priming")
    ax.set_xticks(x)
    ax.set_xticklabels(files, rotation=45, ha="right")
    ax.set_ylabel("Correctly decoded prefix (bytes)")
    ax.set_title("Plaintext Leak Under a Wrong Key: Priming OFF vs ON")
    ax.legend()
    save(fig, "graph3_leak_comparison.png")


def graph_heatmap(df):
    """Similarity per file and scenario."""
    pivot = df.pivot_table(index="file", columns="label",
                           values="similarity", aggfunc="mean",
                           observed=True)
    pivot = pivot.reindex(columns=[c for c in LABEL_ORDER
                                   if c in pivot.columns])

    fig, ax = plt.subplots(figsize=(10, max(4, len(pivot) * 0.5)))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn",
                   vmin=0, vmax=100)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            if pd.notna(val):
                ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                        fontsize=8, fontweight="bold")

    fig.colorbar(im).set_label("Similarity (%)")
    ax.set_title("Similarity Heatmap per File and Scenario")
    save(fig, "graph4_heatmap.png")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    df = load_data()
    graph_similarity(df)
    graph_failure_distance(df)
    graph_leak_comparison(df)
    graph_heatmap(df)


if __name__ == "__main__":
    main()
