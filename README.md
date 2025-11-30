<div align="center">

🚀 rANS Data Compression Study

A Comparative Analysis & Implementation of Asymmetric Numeral Systems

</div>


Data Compression is the art of representing information using fewer bits. Traditional methods like Huffman Coding are fast but not optimal (they use whole bits), while Arithmetic Coding is optimal but slow (complex math).

rANS (Asymmetric Numeral Systems) is a game-changer. It combines the best of both worlds:

High Compression Ratio: Approaching the theoretical limit (Entropy), similar to Arithmetic Coding.

High Speed: Fast encoding/decoding using simple arithmetic operations, similar to Huffman.

This repository contains two complete implementations of rANS, built from scratch to demonstrate both the educational theory and the industrial power of the algorithm.

🧠 How rANS Works (The Core Magic)

The heart of our project relies on the ryg_rans library by Fabian Giesen. Here is a simplified explanation of what happens under the hood:

1. The Concept of "State"

Imagine a single large number, let's call it x (the State). This number holds the entire compressed file. To compress a new symbol (like the letter 'A'), we mathematically "push" it into x, creating a new, slightly larger x.

2. Encoding (Compression)

We process the file backwards (from the last byte to the first).

Input: The current state x and the symbol to compress.

Action: We use the symbol's probability (frequency) to determine a range. Frequent symbols get larger ranges, rare symbols get smaller ranges.

Math: x_new = C(x, symbol_frequency).

Result: A new state that encodes both the previous data and the new symbol.

3. Decoding (Decompression)

We process forwards.

Input: The final state x.

Action: We look at where x falls in our probability ranges to figure out what the last encoded symbol was.

Math: symbol = D(x), x_prev = D_state(x).

Result: We output the symbol and get back the previous state, ready to decode the next symbol.

4. Normalization (Renormalization)

Since x grows infinitely, computers can't hold it in a standard variable (32/64 bit).

Solution: Whenever x gets too big, we stream out the lower bits to the file (write them to disk) and keep x small. This ensures we can compress gigabytes of data using fixed memory.

📂 Project Architecture

We implemented two distinct versions to study the algorithm:

1. rygransProject (Educational Core)

Purpose: To learn and demonstrate the algorithm cleanly.

Base: ryg_rans header-only library.

Key Files:

main.cpp: The Driver. It manages file I/O, builds the frequency table (histogram), and calls the rANS functions.

rans_byte.h: The Engine. Contains the mathematical macros and functions for the rANS state machine.

run_benchmark.bat: The Automator. A script that compiles the code and runs tests on multiple files automatically.

2. HtsCodecsProject (Industrial Performance)

Purpose: To achieve maximum speed and efficiency.

Base: htscodecs (used in DNA sequencing compression).

Features: Optimized bit-packing, dynamic memory management, and support for Order-1 context modeling (predicting the next character based on the previous one).

🛠️ Installation Guide

Follow these exact steps to set up the environment on Windows.

Step 1: Install a C++ Compiler (TDM-GCC)

You need a tool to turn the C++ code into an executable program (.exe).

Download: Get TDM-GCC (a lightweight compiler for Windows) from the following URL:
https://github.com/jmeubank/tdm-gcc/releases/download/v10.3.0-tdm64-2/tdm64-gcc-10.3.0-2.exe

Install:

Run the installer.

Click Create.

Choose MinGW-w64/TDM64 (32-bit and 64-bit).

CRITICAL STEP: Ensure the checkbox "Add to PATH" is checked. This allows your computer to find the compiler command g++.

Click Install.

Step 2: Download the Project

Click the green Code button at the top of this GitHub page.

Select Download ZIP.

Extract the ZIP file to your Desktop or Documents folder.

🚀 Usage Instructions

We have automated the entire process. You don't need to write complex commands.

Running the Benchmark

Open the project folder (ANS-Compression-Study).

Go to one of the project subfolders (e.g., rygransProject).

Double-click the file named run_benchmark.bat.

What happens next?

Build: The script automatically calls g++ to compile main.cpp into compressor.exe.

Compress: It scans the cantrbry folder (which contains test files like books, spreadsheets, and code) and compresses them one by one.

Report: It opens a newly generated Excel CSV file (Compression_Results.csv) showing you the original size, compressed size, and savings percentage.

Conclusion:
The rANS algorithm proves to be highly effective, especially on files with low entropy (like images or spreadsheets), achieving up to 84% reduction in size. Even for standard text (like Alice in Wonderland), it consistently saves over 40% of disk space without losing a single bit of information.

<br />

<div align="center">

Developed by Matan Elevavi • Ariel University • 2025

</div>
