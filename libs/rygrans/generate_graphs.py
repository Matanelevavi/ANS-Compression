"""
generate_graphs.py — Encryption Test Visualization
Research-oriented graphs for encryption experiments.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# Paths
# ==========================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

CSV_PATH   = os.path.join(ROOT_DIR, "results", "encryption_tests", "encryption_results.csv")
OUTPUT_DIR = os.path.join(ROOT_DIR, "results", "encryption_tests")

# ==========================================
# Design
# ==========================================

PALETTE = {
    "No key": "#2196F3",
    "Correct key": "#4CAF50",
    "Wrong key": "#F44336",
    "One-bit flip (pos 100)": "#FF9800",
}

LABEL_ORDER = [
    "No key",
    "Correct key",
    "Wrong key",
    "One-bit flip (pos 100)"
]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.grid": True,
    "axes.axisbelow": True
})

# ==========================================
# Helpers
# ==========================================

def load_data():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)

    df["label"] = pd.Categorical(
        df["label"],
        categories=LABEL_ORDER,
        ordered=True
    )

    return df


def save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {name}")

# ==========================================
# Graph 1
# Similarity by Scenario
# ==========================================

def graph_similarity(df):

    agg = (
        df.groupby("label", observed=True)["similarity"]
        .mean()
        .reindex(LABEL_ORDER)
    )

    fig, ax = plt.subplots(figsize=(8,5))

    colors = [PALETTE[x] for x in agg.index]

    bars = ax.bar(
        agg.index,
        agg.values,
        color=colors
    )

    for b, v in zip(bars, agg.values):
        ax.text(
            b.get_x() + b.get_width()/2,
            v + 1,
            f"{v:.1f}%",
            ha="center",
            fontweight="bold"
        )

    ax.set_ylim(0,110)

    ax.set_ylabel("Similarity (%)")
    ax.set_title("Average Similarity to Original File")

    save(fig, "graph1_similarity.png")

# ==========================================
# Graph 2
# Failure Distance
# ==========================================

def graph_failure_distance(df):

    err = df[
        df["label"].isin([
            "Wrong key",
            "One-bit flip (pos 100)"
        ])
    ]

    fig, ax = plt.subplots(figsize=(9,5))

    x_map = {
        "Wrong key": 0,
        "One-bit flip (pos 100)": 1
    }

    for label in x_map:

        subset = err[err["label"] == label]

        x = np.random.normal(
            x_map[label],
            0.04,
            len(subset)
        )

        ax.scatter(
            x,
            subset["match_prefix"],
            s=60,
            color=PALETTE[label],
            alpha=0.8,
            label=label
        )

    ax.axhline(
        100,
        linestyle="--",
        color="black",
        alpha=0.7,
        label="Bit Flip Location"
    )

    ax.set_xticks([0,1])
    ax.set_xticklabels([
        "Wrong Key",
        "One-Bit Flip"
    ])

    ax.set_ylabel("Matching Prefix Length (bytes)")
    ax.set_title("Failure Distance Before Divergence")

    ax.legend()

    save(fig, "graph2_failure_distance.png")

# ==========================================
# Graph 3
# Similarity Distribution
# ==========================================

def graph_similarity_distribution(df):

    wrong = df[df["label"] == "Wrong key"]["similarity"]
    flip  = df[df["label"] == "One-bit flip (pos 100)"]["similarity"]

    fig, ax = plt.subplots(figsize=(8,5))

    ax.hist(
        wrong,
        bins=10,
        alpha=0.7,
        color=PALETTE["Wrong key"],
        label="Wrong Key"
    )

    ax.hist(
        flip,
        bins=10,
        alpha=0.7,
        color=PALETTE["One-bit flip (pos 100)"],
        label="One-Bit Flip"
    )

    ax.set_xlabel("Similarity (%)")
    ax.set_ylabel("Number of Files")

    ax.set_title(
        "Similarity Distribution Under Key Errors"
    )

    ax.legend()

    save(fig, "graph3_similarity_distribution.png")

# ==========================================
# Graph 4
# Heatmap
# ==========================================

def graph_heatmap(df):

    pivot = df.pivot_table(
        index="file",
        columns="label",
        values="similarity",
        aggfunc="mean",
        observed=True
    )

    pivot = pivot.reindex(columns=LABEL_ORDER)

    fig, ax = plt.subplots(
        figsize=(10, max(4, len(pivot)*0.5))
    )

    im = ax.imshow(
        pivot.values,
        aspect="auto",
        cmap="RdYlGn",
        vmin=0,
        vmax=100
    )

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(
        pivot.columns,
        rotation=20,
        ha="right"
    )

    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):

            val = pivot.iloc[i, j]

            if pd.notna(val):
                ax.text(
                    j,
                    i,
                    f"{val:.0f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    fontweight="bold"
                )

    cbar = fig.colorbar(im)
    cbar.set_label("Similarity (%)")

    ax.set_title(
        "Similarity Heatmap per File and Scenario"
    )

    save(fig, "graph4_heatmap.png")

# ==========================================
# Main
# ==========================================

def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = load_data()

    graph_similarity(df)
    graph_failure_distance(df)
    graph_similarity_distribution(df)
    graph_heatmap(df)


if __name__ == "__main__":
    main()