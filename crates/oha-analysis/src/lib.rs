//! Bounded, content-oriented sampling metrics for OHA research.
//!
//! High byte entropy alone is not evidence of incompressibility.

use std::fs::File;
use std::io::{self, Read, Seek, SeekFrom};
use std::path::Path;

const SAMPLE_CHUNK: u64 = 64 * 1024;
const MAX_SAMPLE: u64 = 3 * SAMPLE_CHUNK;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContentHint {
    Empty,
    MostlyText,
    Binary,
}

#[derive(Debug, Clone)]
pub struct SampleStats {
    pub input_bytes: u64,
    pub sampled_bytes: usize,
    pub entropy_bits_per_byte: f64,
    pub ascii_ratio: f64,
    pub zero_ratio: f64,
    pub unique_byte_values: usize,
    pub hint: ContentHint,
}

fn is_text_byte(byte: u8) -> bool {
    byte.is_ascii_graphic() || byte == b' ' || matches!(byte, b'\n' | b'\r' | b'\t')
}

fn malformed_utf8_sequences(mut remaining: &[u8]) -> usize {
    let mut count = 0;
    while let Err(error) = std::str::from_utf8(remaining) {
        count += 1;
        let advance = error.valid_up_to()
            + error
                .error_len()
                .unwrap_or(remaining.len() - error.valid_up_to());
        remaining = &remaining[advance..];
    }
    count
}

/// Compute descriptive metrics; never skip a compression trial solely on these metrics.
pub fn analyze_bytes(bytes: &[u8]) -> SampleStats {
    if bytes.is_empty() {
        return SampleStats {
            input_bytes: 0,
            sampled_bytes: 0,
            entropy_bits_per_byte: 0.0,
            ascii_ratio: 0.0,
            zero_ratio: 0.0,
            unique_byte_values: 0,
            hint: ContentHint::Empty,
        };
    }

    let mut counts = [0_usize; 256];
    let mut ascii = 0_usize;
    let mut zeros = 0_usize;
    for &byte in bytes {
        counts[byte as usize] += 1;
        ascii += usize::from(is_text_byte(byte));
        zeros += usize::from(byte == 0);
    }
    let length = bytes.len() as f64;
    let entropy = counts
        .iter()
        .filter(|&&c| c > 0)
        .map(|&c| {
            let p = c as f64 / length;
            -p * p.log2()
        })
        .sum();
    let ratio = ascii as f64 / length;
    let decoded = String::from_utf8_lossy(bytes);
    let mut decoded_count = 0_usize;
    let malformed_sequences = malformed_utf8_sequences(bytes);
    let mut invalid_controls = 0_usize;
    for character in decoded.chars() {
        decoded_count += 1;
        invalid_controls +=
            usize::from(character.is_control() && !matches!(character, '\n' | '\r' | '\t'));
    }
    let likely_text = zeros == 0
        && (malformed_sequences as f64 / decoded_count as f64) < 0.01
        && (invalid_controls as f64 / decoded_count as f64) < 0.05;
    SampleStats {
        input_bytes: bytes.len() as u64,
        sampled_bytes: bytes.len(),
        entropy_bits_per_byte: entropy,
        ascii_ratio: ratio,
        zero_ratio: zeros as f64 / length,
        unique_byte_values: counts.iter().filter(|&&c| c != 0).count(),
        hint: if likely_text {
            ContentHint::MostlyText
        } else {
            ContentHint::Binary
        },
    }
}

/// Read at most 192 KiB from an arbitrary file using three spaced windows.
/// The result is a sample, not an exhaustive classification.
pub fn analyze_file(path: &Path) -> io::Result<SampleStats> {
    let mut file = File::open(path)?;
    let metadata = file.metadata()?;
    if !metadata.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "regular file required",
        ));
    }
    let original_size = metadata.len();
    let mut buffer = Vec::with_capacity(original_size.min(MAX_SAMPLE) as usize);
    if original_size <= MAX_SAMPLE {
        file.take(MAX_SAMPLE).read_to_end(&mut buffer)?;
    } else {
        let positions = [
            0_u64,
            (original_size / 2).saturating_sub(SAMPLE_CHUNK / 2),
            original_size - SAMPLE_CHUNK,
        ];
        for offset in positions {
            file.seek(SeekFrom::Start(offset))?;
            let mut window = vec![0_u8; SAMPLE_CHUNK as usize];
            file.read_exact(&mut window)?;
            buffer.extend_from_slice(&window);
        }
    }
    let mut stats = analyze_bytes(&buffer);
    stats.input_bytes = original_size;
    Ok(stats)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_input() {
        let r = analyze_bytes(&[]);
        assert_eq!(r.hint, ContentHint::Empty);
        assert_eq!(r.sampled_bytes, 0);
    }

    #[test]
    fn text_and_zero_bytes() {
        assert_eq!(
            analyze_bytes(b"hello world\n").hint,
            ContentHint::MostlyText
        );
        assert_eq!(analyze_bytes(&[0_u8; 256]).hint, ContentHint::Binary);
    }

    #[test]
    fn utf8_text_is_not_classified_as_binary() {
        let text = "Привет, это текст для проверки!\n".repeat(100);
        assert_eq!(analyze_bytes(text.as_bytes()).hint, ContentHint::MostlyText);
    }


    #[test]
    fn valid_unicode_replacement_character_is_text() {
        // U+FFFD is a legitimate character, not proof of malformed UTF-8.
        let input = "\u{fffd}".repeat(500);
        assert_eq!(malformed_utf8_sequences(input.as_bytes()), 0);
        assert_eq!(analyze_bytes(input.as_bytes()).hint, ContentHint::MostlyText);
    }

    #[test]
    fn malformed_utf8_sequences_are_counted_separately() {
        let mixed = format!("{}{}", "\u{fffd}".repeat(100), "\u{fffd}");
        assert_eq!(malformed_utf8_sequences(mixed.as_bytes()), 0);
        let mut bytes = mixed.into_bytes();
        bytes.push(0xff);
        assert_eq!(malformed_utf8_sequences(&bytes), 1);
        assert_eq!(analyze_bytes(&bytes).hint, ContentHint::MostlyText);
        assert_eq!(malformed_utf8_sequences(&[0xff; 100]), 100);
        assert_eq!(analyze_bytes(&[0xff; 100]).hint, ContentHint::Binary);
    }

    #[test]
    fn constant_bytes_have_zero_entropy() {
        let r = analyze_bytes(&[b'Q'; 2048]);
        assert!(r.entropy_bits_per_byte.abs() < f64::EPSILON);
        assert_eq!(r.unique_byte_values, 1);
    }

    #[test]
    fn two_equiprobable_values_have_one_bit_entropy() {
        let r = analyze_bytes(&[0_u8, 1_u8, 0_u8, 1_u8]);
        assert!((r.entropy_bits_per_byte - 1.0).abs() < 0.001);
    }
}
