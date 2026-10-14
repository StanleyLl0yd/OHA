//! Experimental, bounded OHA C ABI for native interface research (M0).
//! This interface analyzes caller-provided memory only; it never creates archives.

use std::mem::size_of;
use std::slice;

const ABI_VERSION: u32 = 1;
const MAX_INPUT_BYTES: u64 = 192 * 1024;

pub const OHA_OK: i32 = 0;
pub const OHA_ERR_NULL_OUTPUT: i32 = 1;
pub const OHA_ERR_NULL_INPUT: i32 = 2;
pub const OHA_ERR_INPUT_TOO_LARGE: i32 = 3;
pub const OHA_ERR_UNSUPPORTED_LAYOUT: i32 = 4;
pub const OHA_ERR_PANIC: i32 = 5;

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct OhaAnalysisV1 {
    pub struct_size: u32,
    pub version: u32,
    pub input_bytes: u64,
    pub sampled_bytes: u64,
    pub entropy_bits_per_byte: f64,
    pub ascii_ratio: f64,
    pub zero_ratio: f64,
    pub unique_byte_values: u32,
    pub content_hint: u32,
    pub reserved: [u64; 2],
}

impl Default for OhaAnalysisV1 {
    fn default() -> Self {
        Self {
            struct_size: size_of::<Self>() as u32,
            version: ABI_VERSION,
            input_bytes: 0,
            sampled_bytes: 0,
            entropy_bits_per_byte: 0.0,
            ascii_ratio: 0.0,
            zero_ratio: 0.0,
            unique_byte_values: 0,
            content_hint: 0,
            reserved: [0; 2],
        }
    }
}

/// ABI version for this research interface, unrelated to `.oha` archive format version.
#[unsafe(no_mangle)]
pub extern "C" fn oha_api_version() -> u32 {
    ABI_VERSION
}

/// Analyze no more than 192 KiB of caller-owned bytes. No pointers are retained.
///
/// # Safety
/// - `output` must point to a valid, writable, correctly aligned `OhaAnalysisV1`.
/// - If `length > 0`, `input` must be valid for reads of `length` consecutive bytes.
/// - Input and output storage must not overlap, and concurrent callers must not mutate them.
/// - Non-null but invalid pointers are programmer errors and cannot be detected reliably.
/// - Passing a null input with length zero is valid.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn oha_analyze_bytes_v1(
    input: *const u8,
    length: u64,
    output: *mut OhaAnalysisV1,
) -> i32 {
    std::panic::catch_unwind(|| {
        // SAFETY: the caller must satisfy the documented pointer preconditions.
        unsafe { analyze_impl(input, length, output) }
    })
    .unwrap_or(OHA_ERR_PANIC)
}

unsafe fn analyze_impl(input: *const u8, length: u64, output: *mut OhaAnalysisV1) -> i32 {
    if output.is_null() {
        return OHA_ERR_NULL_OUTPUT;
    }
    if length > MAX_INPUT_BYTES {
        return OHA_ERR_INPUT_TOO_LARGE;
    }
    if length > 0 && input.is_null() {
        return OHA_ERR_NULL_INPUT;
    }
    // SAFETY: output validity, alignment and exclusivity are caller requirements.
    let (layout_size, version) = unsafe { ((*output).struct_size, (*output).version) };
    if layout_size as usize != size_of::<OhaAnalysisV1>() || version != ABI_VERSION {
        return OHA_ERR_UNSUPPORTED_LAYOUT;
    }
    let bytes: &[u8] = if length == 0 {
        &[]
    } else {
        // SAFETY: length is bounded and the caller owns readable input memory.
        unsafe { slice::from_raw_parts(input, length as usize) }
    };
    let stats = oha_analysis::analyze_bytes(bytes);
    let result = OhaAnalysisV1 {
        input_bytes: stats.input_bytes,
        sampled_bytes: stats.sampled_bytes as u64,
        entropy_bits_per_byte: stats.entropy_bits_per_byte,
        ascii_ratio: stats.ascii_ratio,
        zero_ratio: stats.zero_ratio,
        unique_byte_values: stats.unique_byte_values as u32,
        content_hint: match stats.hint {
            oha_analysis::ContentHint::Empty => 0,
            oha_analysis::ContentHint::MostlyText => 1,
            oha_analysis::ContentHint::Binary => 2,
        },
        ..OhaAnalysisV1::default()
    };
    // SAFETY: output is writable and does not overlap the input memory.
    unsafe { output.write(result) };
    OHA_OK
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ptr;

    #[test]
    fn stable_c_layout() {
        assert_eq!(size_of::<OhaAnalysisV1>(), 72);
        assert_eq!(std::mem::align_of::<OhaAnalysisV1>(), 8);
        assert_eq!(std::mem::offset_of!(OhaAnalysisV1, content_hint), 52);
        assert_eq!(std::mem::offset_of!(OhaAnalysisV1, reserved), 56);
        assert_eq!(oha_api_version(), 1);
    }

    #[test]
    fn empty_and_text_and_binary() {
        let mut output = OhaAnalysisV1::default();
        assert_eq!(unsafe { oha_analyze_bytes_v1(ptr::null(), 0, &mut output) }, OHA_OK);
        assert_eq!(output.content_hint, 0);
        assert_eq!(output.sampled_bytes, 0);
        let text = b"hello from OHA\n";
        assert_eq!(unsafe { oha_analyze_bytes_v1(text.as_ptr(), text.len() as u64, &mut output) }, OHA_OK);
        assert_eq!(output.content_hint, 1);
        let zeros = [0_u8; 100];
        assert_eq!(unsafe { oha_analyze_bytes_v1(zeros.as_ptr(), zeros.len() as u64, &mut output) }, OHA_OK);
        assert_eq!(output.content_hint, 2);
        assert_eq!(output.reserved, [0, 0]);
    }

    #[test]
    fn invalid_metadata_and_pointers() {
        let mut output = OhaAnalysisV1::default();
        let bytes = b"xyz";
        assert_eq!(unsafe { oha_analyze_bytes_v1(bytes.as_ptr(), 3, ptr::null_mut()) }, OHA_ERR_NULL_OUTPUT);
        assert_eq!(unsafe { oha_analyze_bytes_v1(ptr::null(), 1, &mut output) }, OHA_ERR_NULL_INPUT);
        assert_eq!(unsafe { oha_analyze_bytes_v1(ptr::null(), MAX_INPUT_BYTES + 1, &mut output) }, OHA_ERR_INPUT_TOO_LARGE);
        output.version = 2;
        assert_eq!(unsafe { oha_analyze_bytes_v1(bytes.as_ptr(), 3, &mut output) }, OHA_ERR_UNSUPPORTED_LAYOUT);
        output.version = 1;
        output.struct_size = 1;
        assert_eq!(unsafe { oha_analyze_bytes_v1(bytes.as_ptr(), 3, &mut output) }, OHA_ERR_UNSUPPORTED_LAYOUT);
    }
}
