import os
import subprocess
import time
import csv
import platform
import sys

# --- Configuration Constants ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

EXE_NAME = "compressor.exe" if platform.system() == "Windows" else "compressor"

EXE_PATH = os.path.join(SCRIPT_DIR, EXE_NAME)
DATASET_PURE = os.path.join(SCRIPT_DIR, "..", "..", "files", "smallFiles")
DATASET_ENC  = os.path.join(SCRIPT_DIR, "..", "..", "files", "50MFiles")
LOG_CSV      = os.path.join(SCRIPT_DIR, "..", "..", "results", "Rygrans_Results.csv")

def run_simulation(dataset_path, dataset_name, writer):
    """Iterates over a files dataset and benchmarks compression/decompression."""
    if not os.path.exists(dataset_path):
        print(f"  [Warning] Dataset path not found: {dataset_path}")
        return

    for filename in os.listdir(dataset_path):
        file_path = os.path.join(dataset_path, filename)
        
        # Skip directories and special files
        if os.path.isdir(file_path) or filename.startswith("."):
            continue
            
        original_size = os.path.getsize(file_path)
        comp_path = f"{filename}.rans"
        restored_path = "temp_restored.bin"

        # Clean old remains if they exist
        if os.path.exists(comp_path): os.remove(comp_path)
        if os.path.exists(restored_path): os.remove(restored_path)

        try:
            # --- 1. Execution Pass: Compression ---
            # Cleaned up: only passing mode, input, and output paths
            cmd_c = [str(EXE_PATH), "c", str(file_path), str(comp_path)]
            
            start_time = time.perf_counter()
            subprocess.run(cmd_c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            end_time = time.perf_counter()
            
            comp_time = round((end_time - start_time) * 1000, 2)  # Milliseconds
            compressed_size = os.path.getsize(comp_path)

            # --- 2. Execution Pass: Decompression ---
            # Cleaned up: only passing mode, input, and output paths
            cmd_d = [str(EXE_PATH), "d", str(comp_path), str(restored_path)]
            
            start_time = time.perf_counter()
            subprocess.run(cmd_d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            end_time = time.perf_counter()
            
            decomp_time = round((end_time - start_time) * 1000, 2)  # Milliseconds

            # --- 3. Windows Binary Verification Flow ---
            # Uses fc.exe /b via cmd shell to verify perfect bitwise reconstruction
            with open(file_path, "rb") as f1, open(restored_path, "rb") as f2:
                is_identical = (f1.read() == f2.read())

            if is_identical:
                # Math metrics
                if original_size == 0:
                    ratio = 0
                    savings = 0
                else:
                    ratio = round((compressed_size / original_size) * 100, 2)
                    savings = round((1 - compressed_size / original_size) * 100, 2)
                status = "SUCCESS"
                print(f"  Processed: {filename}     Decompression Is Match ")
            else:
                savings, ratio, comp_time, decomp_time = 0.0, 0.0, 0.0, 0.0
                status = "INTEGRITY ERROR"
                print(f"  Processed: {filename} (!!! INTEGRITY ERROR: Decompression Mismatch !!!)")

            # Save stats locally inside results CSV matrix
            writer.writerow([
                dataset_name, filename, original_size, compressed_size, 
                ratio, savings, comp_time, decomp_time, status
            ])

        except subprocess.CalledProcessError:
            print(f"  [Runtime Error] Pipeline broke processing: {filename}")
        finally:
            # Housekeeping: erase local disk runtime artifacts
            if os.path.exists(comp_path): os.remove(comp_path)
            if os.path.exists(restored_path): os.remove(restored_path)

def build():
    sources = [
        "main.cpp",
        "EncryptionKey.cpp",
        "AdaptiveModel.cpp",
        "Compressor.cpp",
        "Decompressor.cpp",
    ]
    sources = [os.path.join(SCRIPT_DIR, s) for s in sources]
    cmd = ["g++", "-O3"] + sources + ["-o", EXE_PATH]
    result = subprocess.run(cmd, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stderr.decode())
        sys.exit(1)
def main():
    build()   
    # Rebuilding output directory schema if missing
    os.makedirs(os.path.dirname(LOG_CSV), exist_ok=True)

    with open(LOG_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Structural CSV Row Header Format
        writer.writerow([
            "Dataset", "Filename", "Original_Size", "Compressed_Size", 
            "Ratio_Percent", "Savings_Percent", "Comp_Time_MS", "Decomp_Time_MS", "Status"
        ])

        print(f"Streaming small files tests...")
        run_simulation(DATASET_PURE, "smallFiles", writer)

        print(f"\nStreaming 50MFiles files tests...")
        run_simulation(DATASET_ENC, "50MFiles", writer)

if __name__ == "__main__":
    main()
