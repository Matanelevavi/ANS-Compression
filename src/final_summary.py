import pandas as pd
import os
import matplotlib.pyplot as plt

ARITH_REPORT = "results/Final_Comparison_Report.csv"
HTS_REPORT = "results/HTSCodecs_Results.csv"
OUTPUT_MASTER = "results/Master_Comparison_Table.csv"
OUTPUT_GRAPH = "results/comparison_graph.png"

def generate_summary():
    print("🚀 Generating Final Summary...")
    
    if not os.path.exists(ARITH_REPORT) or not os.path.exists(HTS_REPORT):
        print(f"❌ Error: Missing files.")
        return

    # 1. טעינת דוח ה-Arithmetic
    df_arith = pd.read_csv(ARITH_REPORT)
    df_arith.columns = df_arith.columns.str.strip()
    
    # מיפוי שמות עמודות ל-Arith (כולל הגדלים החדשים)
    df_arith = df_arith.rename(columns={
        'File Name': 'File_Name',
        'Original Size': 'Original_Size', # כדי שיהיה אחיד
        'Rygrans Size': 'Rygrans_Size',   # חדש
        'Ref Arith Size': 'Ref_Arith_Size', # חדש
        'Your ANS Ratio (%)': 'Rygrans_ANS',
        'Ref Arith Ratio (%)': 'Ref_Arith'
    })

    # 2. טעינת דוח ה-HTSCodecs
    df_hts = pd.read_csv(HTS_REPORT)
    df_hts.columns = df_hts.columns.str.strip()
    
    # מיפוי שמות עמודות ל-HTS
    df_hts = df_hts.rename(columns={
        'Filename': 'File_Name',
        'Compressed_Size': 'HTS_Size', # נקרא לזה HTS_Size כדי לא לבלבל
        'Ratio_Percent': 'HTSCodecs_ANS'
    })

    # 3. מיזוג הטבלאות
    print(f"DEBUG - Arith columns: {list(df_arith.columns)}")
    print(f"DEBUG - HTS columns: {list(df_hts.columns)}")

    try:
        # בוחרים אילו עמודות לקחת מכל דוח
        cols_arith = ['File_Name', 'Original_Size', 'Rygrans_Size', 'Ref_Arith_Size', 'Rygrans_ANS', 'Ref_Arith']
        cols_hts = ['File_Name', 'HTS_Size', 'HTSCodecs_ANS']
        
        # המיזוג מתבצע לפי שם הקובץ
        master_df = pd.merge(
            df_arith[cols_arith],
            df_hts[cols_hts],
            on='File_Name'
        )
    except KeyError as e:
        print(f"❌ Merge failed. Required columns missing: {e}")
        return

    # שמירת התוצאות לטבלה המסכמת
    os.makedirs("results", exist_ok=True)
    master_df.to_csv(OUTPUT_MASTER, index=False)
    print(f"✅ Master table saved to: {OUTPUT_MASTER}")

    # 4. יצירת הגרף (ללא שורת ה-TOTAL)
    # אנחנו מסננים החוצה את השורה שבה שם הקובץ הוא TOTAL לצורך הגרף
    graph_df = master_df[master_df['File_Name'] != 'TOTAL']

    plt.figure(figsize=(12, 7))
    plt.plot(graph_df['File_Name'], graph_df['Rygrans_ANS'], marker='o', label='Rygrans ANS (Yours)')
    plt.plot(graph_df['File_Name'], graph_df['HTSCodecs_ANS'], marker='s', label='HTSCodecs ANS')
    plt.plot(graph_df['File_Name'], graph_df['Ref_Arith'], marker='^', linestyle='--', label='Arithmetic Ref')

    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Compression Ratio % (Lower is Better)')
    plt.title('Compression Efficiency: Rygrans vs HTS vs Arith')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(OUTPUT_GRAPH)
    print(f"📊 Graph successfully created: {OUTPUT_GRAPH}")

if __name__ == "__main__":
    generate_summary()