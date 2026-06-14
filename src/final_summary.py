import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

# --- Paths ---

REPORT_FILE = "results/Final_Comparison_Report.csv"

OUTPUT_SMALL = "results/Comparison_Small.csv"
OUTPUT_LARGE = "results/Comparison_Large.csv"

OUTPUT_GRAPH_SMALL = "results/comparison_graph_small.png"
OUTPUT_GRAPH_LARGE = "results/comparison_graph_large.png"


def save_graph(df, output_path, title):

    if df.empty:
        print(f"Skipping graph '{output_path}' because dataframe is empty.")
        return

    x = np.arange(len(df))
    width = 0.35

    plt.figure(figsize=(14, 7))

    # Rygrans
    plt.bar(
        x - width / 2,
        df['Rygrans Ratio (%)'],
        width=width,
        label='Rygrans'
    )

    # Arithmetic
    plt.bar(
        x + width / 2,
        df['Arithmetic Ratio (%)'],
        width=width,
        label='Arithmetic'
    )

    plt.xticks(
        x,
        df['File Name'],
        rotation=45,
        ha='right'
    )

    plt.ylabel('Compression Ratio % (Lower is Better)')

    plt.title(title)

    plt.grid(axis='y', alpha=0.3)

    plt.legend()

    plt.tight_layout()

    plt.savefig(output_path)

    plt.close()

    print(f"Graph created: {output_path}")


def generate_summary():

    if not os.path.exists(REPORT_FILE):
        print("Error: Missing Final_Comparison_Report.csv")
        return

    # Load final report
    df = pd.read_csv(REPORT_FILE)

    df.columns = df.columns.str.strip()

    # Split datasets
    small_df = df[df['Dataset'] == 'smallFiles'].copy()

    large_df = df[df['Dataset'] == '50MFiles'].copy()

    os.makedirs("results", exist_ok=True)

    # Save split CSVs
    small_df.to_csv(OUTPUT_SMALL, index=False)

    large_df.to_csv(OUTPUT_LARGE, index=False)

    # Create graphs
    save_graph(
        small_df,
        OUTPUT_GRAPH_SMALL,
        "Compression Comparison - Small Files"
    )

    save_graph(
        large_df,
        OUTPUT_GRAPH_LARGE,
        "Compression Comparison - Large Files"
    )


if __name__ == "__main__":
    generate_summary()