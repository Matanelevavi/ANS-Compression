#pragma once
#include <string>
#include <cstdint>
#include "EncryptionKey.h" 

// Decompresses input_path into output_path.
//
// seed and dummy_mode must exactly match the values used during compression.
void decompress(const std::string& input_path,  const std::string& output_path, EncryptionKey& enc_key);

