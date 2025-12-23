import os

# מציאת הנתיב המוחלט של תיקיית הפרויקט
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")

print(f"--- Diagnostics ---")
print(f"Project root: {BASE_DIR}")
print(f"Looking for results in: {RESULTS_DIR}")

if not os.path.exists(RESULTS_DIR):
    print("!!! Error: The 'results' folder does not exist at this path.")
else:
    files = os.listdir(RESULTS_DIR)
    print(f"Files found in 'results': {files}")
    
    expected = ["Rygrans_Results.csv", "HTSCodecs_Results.csv", "Final_Comparison_Report.csv"]
    for f in expected:
        if f in files:
            print(f"[V] Found: {f}")
        else:
            print(f"[X] MISSING: {f}")