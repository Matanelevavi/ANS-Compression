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

    # 1. טעינת דוח ה-Arithmetic וניקוי שמות עמודות
    df_arith = pd.read_csv(ARITH_REPORT)
    # הסרת רווחים מיותרים משמות העמודות
    df_arith.columns = df_arith.columns.str.strip()
    
    # מיפוי שמות עמודות ל-Arith (לפי ה-Debug שלך)
    df_arith = df_arith.rename(columns={
        'File Name': 'File_Name',
        'Your ANS Ratio (%)': 'Rygrans_ANS',
        'Ref Arith Ratio (%)': 'Ref_Arith'
    })

    # 2. טעינת דוח ה-HTSCodecs וניקוי שמות עמודות
    df_hts = pd.read_csv(HTS_REPORT)
    df_hts.columns = df_hts.columns.str.strip() # מסיר את הרווח ב-'Savings_Percent '
    
    # מיפוי שמות עמודות ל-HTS (לפי ה-Debug שלך)
    df_hts = df_hts.rename(columns={
        'Filename': 'File_Name',
        'Ratio_Percent': 'HTSCodecs_ANS'
    })

    # 3. מיזוג הטבלאות
    print(f"DEBUG - Arith columns: {list(df_arith.columns)}")
    print(f"DEBUG - HTS columns: {list(df_hts.columns)}")

    try:
        # וידוא קיום עמודות הכרחיות
        cols_arith = ['File_Name', 'Rygrans_ANS', 'Ref_Arith']
        cols_hts = ['File_Name', 'HTSCodecs_ANS']
        
        master_df = pd.merge(
            df_arith[cols_arith],
            df_hts[cols_hts],
            on='File_Name'
        )
    except KeyError as e:
        print(f"❌ Merge failed. Required columns missing: {e}")
        return

    # שמירת התוצאות
    os.makedirs("results", exist_ok=True)
    master_df.to_csv(OUTPUT_MASTER, index=False)
    print(f"✅ Master table saved to: {OUTPUT_MASTER}")

    # 4. יצירת הגרף
    plt.figure(figsize=(12, 7))
    plt.plot(master_df['File_Name'], master_df['Rygrans_ANS'], marker='o', label='Rygrans ANS (Yours)')
    plt.plot(master_df['File_Name'], master_df['HTSCodecs_ANS'], marker='s', label='HTSCodecs ANS')
    plt.plot(master_df['File_Name'], master_df['Ref_Arith'], marker='^', linestyle='--', label='Arithmetic Ref')

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