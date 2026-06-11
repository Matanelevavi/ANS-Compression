import os
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

RYGRANS_DIR = os.path.join(ROOT_DIR, "libs", "rygrans")

BENCHMARK_SCRIPT = os.path.join(RYGRANS_DIR, "run_benchmark.py")


COMPARE_SCRIPT = os.path.join(ROOT_DIR,"reference", "arith", "compare_algorithms.py")

SUMMARY_SCRIPT = os.path.join(ROOT_DIR, "src", "final_summary.py")


def run_step(description, command, working_dir=ROOT_DIR, shell=False):

    print("\n" + "=" * 60)
    print(f"Starting Step: {description}")
    print("=" * 60)

    try:
        subprocess.run(command, cwd=working_dir, shell=shell,  check=True  )

        print(f"\nStep '{description}' completed successfully.")

    except subprocess.CalledProcessError:

        print(f"\nError: Step '{description}' failed!")
        sys.exit(1)


def main():

    print("ANS Compression Project Pipeline\n")

    required_files = [BENCHMARK_SCRIPT, COMPARE_SCRIPT, SUMMARY_SCRIPT]

    for file in required_files:
        if not os.path.exists(file):
            print(f"Missing file: {file}")
            sys.exit(1)
    
    # 1. Run Rygrans Benchmark
    run_step(
        description="Run Rygrans Benchmark",
        command=[sys.executable, BENCHMARK_SCRIPT],
        working_dir=RYGRANS_DIR
    )

    # 2. Generate Comparison CSV
    run_step(
        description="Generate Final Comparison Report",
        command=[sys.executable, COMPARE_SCRIPT],
        working_dir=ROOT_DIR
    )

    # 3. Generate Summary Graphs
    run_step(
        description="Generate Summary Graphs",
        command=[sys.executable, SUMMARY_SCRIPT],
        working_dir=ROOT_DIR
    )


    print("\nALL DONE")
    print(f"Results saved in: {os.path.join(ROOT_DIR, 'results')}")


if __name__ == "__main__":
    main()