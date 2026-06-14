#pragma once
#include <string>
#include <cstdint>
#include "EncryptionKey.h" 

// Compresses input_path into output_path using adaptive block-rANS.
//
// seed       : key seed — must match the decompressor's seed
void compress  (const std::string& input_path,  const std::string& output_path, EncryptionKey& enc_key);

