import pandas as pd
import os
import matplotlib.pyplot as plt

ARITH_REPORT = "results/Final_Comparison_Report.csv"
HTS_REPORT = "results/HTSCodecs_Results.csv"

OUTPUT_SMALL = "results/Comparison_Small.csv"
OUTPUT_LARGE = "results/Comparison_Large.csv"

OUTPUT_GRAPH_SMALL = "results/comparison_graph_small.png"
OUTPUT_GRAPH_LARGE = "results/comparison_graph_large.png"


def save_graph(df, output_path, title):
    if df.empty:
        print(f"⚠️ Skipping graph '{output_path}' because dataframe is empty.")
        return

    import numpy as np

    x = np.arange(len(df))   # מיקום לכל קובץ על ציר X
    width = 0.25             # רוחב כל עמודה

    plt.figure(figsize=(14, 7))

    plt.bar(x - width, df['Rygrans_ANS'], width=width, label='Rygrans ANS (Yours)')
    plt.bar(x, df['HTSCodecs_ANS'], width=width, label='HTSCodecs ANS')
    plt.bar(x + width, df['Ref_Arith'], width=width, label='Arithmetic Ref')

    plt.xticks(x, df['File_Name'], rotation=45, ha='right')
    plt.ylabel('Compression Ratio % (Lower is Better)')
    plt.title(title)
    plt.grid(axis='y', alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f"📊 Bar graph successfully created: {output_path}")


def generate_summary():
    print("🚀 Generating Split Summaries (Small / Large)...")

    if not os.path.exists(ARITH_REPORT) or not os.path.exists(HTS_REPORT):
        print("❌ Error: Missing files.")
        return

    # 1. Load Arithmetic/Rygrans report
    df_arith = pd.read_csv(ARITH_REPORT)
    df_arith.columns = df_arith.columns.str.strip()

    df_arith = df_arith.rename(columns={
    'Dataset': 'Dataset',
    'File Name': 'File_Name',
    'Rygrans ANS Ratio (%)': 'Rygrans_ANS',
    'Ref Arith Ratio (%)': 'Ref_Arith'
    })

    # 2. Load HTS report
    df_hts = pd.read_csv(HTS_REPORT)
    df_hts.columns = df_hts.columns.str.strip()

    df_hts = df_hts.rename(columns={
        'Dataset': 'Dataset',
        'Filename': 'File_Name',
        'Ratio_Percent': 'HTSCodecs_ANS'
    })

    print(f"DEBUG - Arith columns: {list(df_arith.columns)}")
    print(f"DEBUG - HTS columns: {list(df_hts.columns)}")

    try:
        cols_arith = ['Dataset', 'File_Name', 'Rygrans_ANS', 'Ref_Arith']
        cols_hts = ['Dataset', 'File_Name', 'HTSCodecs_ANS']

        merged_df = pd.merge(
            df_arith[cols_arith],
            df_hts[cols_hts],
            on=['Dataset', 'File_Name']
        )
    except KeyError as e:
        print(f"❌ Merge failed. Required columns missing: {e}")
        return

    # Remove possible TOTAL rows if they exist
    merged_df = merged_df[merged_df['Dataset'] != 'TOTAL']

    # Split by dataset
    small_df = merged_df[merged_df['Dataset'].str.lower() == 'cantrbry'].copy()
    large_df = merged_df[merged_df['Dataset'].str.lower() == '50mfiles'].copy()

    os.makedirs("results", exist_ok=True)

    # Save only the split tables
    small_df.to_csv(OUTPUT_SMALL, index=False)
    large_df.to_csv(OUTPUT_LARGE, index=False)

    print(f"✅ Small files table saved to: {OUTPUT_SMALL}")
    print(f"✅ Large files table saved to: {OUTPUT_LARGE}")

    # Save only the split graphs
    save_graph(
        small_df,
        OUTPUT_GRAPH_SMALL,
        "Compression Efficiency - Small Files"
    )

    save_graph(
        large_df,
        OUTPUT_GRAPH_LARGE,
        "Compression Efficiency - Large Files"
    )


if __name__ == "__main__":
    generate_summary()