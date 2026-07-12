"""
run_full.py - master pipeline: build, benchmark, compare, test, plot.

Runs all project steps in order:

  1. run_benchmark.py       build the compressor + benchmark it
  2. compare_algorithms.py  compare against the arithmetic baseline
  3. final_summary.py       comparison CSVs and graphs
  4. test_encryption.py     the five encryption scenarios
  5. generate_graphs.py     encryption test graphs
  6. paper_experiments.py   experiments from the paper (Section 4)

Any failing step stops the pipeline with a non-zero exit code.
"""

import os
import subprocess
import sys

ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
RYGRANS_DIR = os.path.join(ROOT_DIR, "libs", "rygrans")

STEPS = [
    ("Rygrans benchmark",
     os.path.join(RYGRANS_DIR, "run_benchmark.py"), RYGRANS_DIR),
    ("Comparison vs arithmetic coding",
     os.path.join(ROOT_DIR, "reference", "arith", "compare_algorithms.py"), ROOT_DIR),
    ("Summary graphs",
     os.path.join(ROOT_DIR, "src", "final_summary.py"), ROOT_DIR),
    ("Encryption tests",
     os.path.join(RYGRANS_DIR, "test_encryption.py"), RYGRANS_DIR),
    ("Encryption graphs",
     os.path.join(RYGRANS_DIR, "generate_graphs.py"), RYGRANS_DIR),
    ("Paper experiments",
     os.path.join(RYGRANS_DIR, "paper_experiments.py"), RYGRANS_DIR),
]


def run_step(description, script, working_dir):
    print("\n" + "=" * 60, flush=True)
    print(f"Step: {description}", flush=True)
    print("=" * 60, flush=True)
    try:
        subprocess.run([sys.executable, script], cwd=working_dir, check=True)
        print(f"Step '{description}' completed.")
    except subprocess.CalledProcessError:
        print(f"Error: step '{description}' failed!")
        sys.exit(1)


def main():
    missing = [s for _, s, _ in STEPS if not os.path.exists(s)]
    if missing:
        for m in missing:
            print(f"Missing script: {m}")
        sys.exit(1)

    for description, script, working_dir in STEPS:
        run_step(description, script, working_dir)

    print("\nALL DONE")


if __name__ == "__main__":
    main()
