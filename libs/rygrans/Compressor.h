#pragma once
#include <string>
#include "Config.h"
#include "EncryptionKey.h"

// Compress input_path into output_path using adaptive block-rANS
// with key-gated model updates. The chosen params are written into
// the file header. Returns true on success.
bool compress(const std::string& input_path, const std::string& output_path,
              EncryptionKey& enc_key, const CodecParams& params);
