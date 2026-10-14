#ifndef OHA_FFI_H
#define OHA_FFI_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OHA_ABI_VERSION 1u
#define OHA_MAX_SAMPLE_BYTES 196608u
#define OHA_OK 0
#define OHA_ERR_NULL_OUTPUT 1
#define OHA_ERR_NULL_INPUT 2
#define OHA_ERR_INPUT_TOO_LARGE 3
#define OHA_ERR_UNSUPPORTED_LAYOUT 4
#define OHA_ERR_PANIC 5
#define OHA_HINT_EMPTY 0u
#define OHA_HINT_MOSTLY_TEXT 1u
#define OHA_HINT_BINARY 2u

typedef struct OhaAnalysisV1 {
    uint32_t struct_size;
    uint32_t version;
    uint64_t input_bytes;
    uint64_t sampled_bytes;
    double entropy_bits_per_byte;
    double ascii_ratio;
    double zero_ratio;
    uint32_t unique_byte_values;
    uint32_t content_hint;
    uint64_t reserved[2];
} OhaAnalysisV1;

uint32_t oha_api_version(void);
/* output must be valid, aligned and initialized with struct_size and version.
   input must be valid for length bytes unless length == 0; the regions must
   not overlap and must remain unmodified during this synchronous call. */
int32_t oha_analyze_bytes_v1(const uint8_t *input, uint64_t length,
                             OhaAnalysisV1 *output);

#ifdef __cplusplus
}
#endif
#endif
