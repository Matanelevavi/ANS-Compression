#pragma once
#include <string>
#include "EncryptionKey.h"

// Decompress input_path into output_path. All codec settings
// (rebuild interval, priming, swaps) are read from the file header.
// The key is taken from enc_key if given, otherwise from the seed
// stored in the header. Returns true on success.
bool decompress(const std::string& input_path, const std::string& output_path,
                EncryptionKey& enc_key);
