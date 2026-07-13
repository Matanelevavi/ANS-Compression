"""
download_corpus.py - fetch the 50MB benchmark files from their public
source, the Pizza&Chili Corpus (http://pizzachili.dcc.uchile.cl).

These are large, standard research files (used in many compression
papers), so they are not meant to live in this repository's git
history forever. Run this script once to populate this folder.

If the files are already present (as they are in this checkout for
now), the script does nothing.
"""

import gzip
import os
import shutil
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_URL = "http://pizzachili.dcc.uchile.cl/texts"

# (output filename, source path under BASE_URL)
FILES = [
    ("dna.50MB",       "dna/dna.50MB.gz"),
    ("english.50MB",   "nlang/english.50MB.gz"),
    ("proteins.50MB",  "protein/proteins.50MB.gz"),
    ("sources.50MB",   "code/sources.50MB.gz"),
    ("pitches.50MB",   "music/pitches.50MB.gz"),
    ("dblp.xml.50MB",  "xml/dblp.xml.50MB.gz"),
]


def download_and_unzip(filename, source_path):
    dest = os.path.join(SCRIPT_DIR, filename)
    if os.path.exists(dest):
        print(f"  already present: {filename}")
        return

    url = f"{BASE_URL}/{source_path}"
    gz_path = dest + ".gz"
    print(f"  downloading {filename} from {url}")
    try:
        with urllib.request.urlopen(url, timeout=60) as response, \
             open(gz_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception as e:
        print(f"  [FAILED] {filename}: {e}")
        print(f"  You can also download it manually from {url}")
        if os.path.exists(gz_path):
            os.remove(gz_path)
        return

    with gzip.open(gz_path, "rb") as f_in, open(dest, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(gz_path)
    print(f"  done: {filename} ({os.path.getsize(dest):,} bytes)")


def main():
    print("Fetching the 50MB corpus (Pizza&Chili)...")
    for filename, source_path in FILES:
        download_and_unzip(filename, source_path)

    missing = [f for f, _ in FILES
               if not os.path.exists(os.path.join(SCRIPT_DIR, f))]
    if missing:
        print(f"\nStill missing: {', '.join(missing)}")
        print("Place them manually in files/50MFiles/ or retry this script.")
        sys.exit(1)

    print("\nAll files present.")


if __name__ == "__main__":
    main()
