import os
import subprocess
import sys

# --- Define Paths ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to Rygrans (Your Engine) Benchmark
RYGRANS_DIR = os.path.join(ROOT_DIR, "libs", "rygrans")
RYGRANS_BAT = "run_benchmark.bat"

# Path to HTSCodecs Benchmark
HTS_DIR = os.path.join(ROOT_DIR, "libs", "htscodecs")
HTS_BAT = "run_benchmark.bat"

# Paths to Python Analysis Scripts
COMPARE_SCRIPT = os.path.join(ROOT_DIR, "reference", "arith", "compare_algorithms.py")
SUMMARY_SCRIPT = os.path.join(ROOT_DIR, "src", "final_summary.py")

def run_step(description, command, working_dir=ROOT_DIR, shell=False):
    """Executes a command and prints its status."""
    print(f"\n{'='*60}")
    print(f"🚀 Starting Step: {description}")
    print(f"📂 Working Directory: {working_dir}")
    print(f"{'='*60}")
    
    try:
        # Run the command
        subprocess.run(command, cwd=working_dir, shell=shell, check=True)
        print(f"\n✅ Step '{description}' completed successfully.")
    except subprocess.CalledProcessError:
        print(f"\n❌ Error: Step '{description}' failed!")
        sys.exit(1) # Stop execution if a step fails

def main():
    print("--- ANS Compression Project: Full Automation Pipeline ---\n")

    # 1. Run Rygrans Benchmark (Creates the compressed .rans files)
    # We use shell=True to execute the .bat file
    run_step(
        description="Run Rygrans Benchmark (Generate Compressed Files)",
        command=RYGRANS_BAT,
        working_dir=RYGRANS_DIR,
        shell=True
    )

    # 2. Run HTSCodecs Benchmark
    run_step(
        description="Build & Benchmark HTSCodecs",
        command=HTS_BAT,
        working_dir=HTS_DIR,
        shell=True
    )

    # 3. Run Comparison (Rygrans vs Arithmetic)
    # Using sys.executable ensures we use the same Python environment
    run_step(
        description="Compare Rygrans vs Arithmetic",
        command=[sys.executable, COMPARE_SCRIPT],
        working_dir=ROOT_DIR
    )

    # 4. Generate Final Summary & Graph
    run_step(
        description="Generate Final Summary & Graph",
        command=[sys.executable, SUMMARY_SCRIPT],
        working_dir=ROOT_DIR
    )

    print("\n🎉🎉🎉 ALL DONE! 🎉🎉🎉")
    print(f"Check the results in: {os.path.join(ROOT_DIR, 'results')}")

if __name__ == "__main__":
    main()