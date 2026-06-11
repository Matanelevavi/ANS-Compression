#pragma once
#include <string>
#include <cstdint>

// Compresses input_path into output_path using adaptive block-rANS.
//
// seed       : key seed — must match the decompressor's seed
void compress(const std::string& input_path,
              const std::string& output_path);
