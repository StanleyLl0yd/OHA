// SPDX-License-Identifier: MPL-2.0
//! Deterministic candidate ranking for OHA's M0 policy research.
//! These inputs are measured outcomes, not codec performance predictions.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Codec {
    Store,
    Zstd,
    Lzma2,
    Bzip3,
}

impl Codec {
    /// Stable tie-break only; not an assertion that a codec compresses better.
    const fn tie_rank(self) -> u8 {
        match self {
            Self::Store => 0,
            Self::Zstd => 1,
            Self::Lzma2 => 2,
            Self::Bzip3 => 3,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub enum Profile {
    Fast,
    Balanced,
    Maximum,
}

#[derive(Debug, Clone, Copy)]
pub struct Candidate {
    pub codec: Codec,
    pub payload_bytes: u64,
    pub metadata_bytes: u64,
    pub encode_ms: u64,
    pub decode_ms: u64,
    pub decoder_memory_bytes: u64,
}

#[derive(Debug, Clone, Copy)]
pub struct Limits {
    pub max_encode_ms: u64,
    pub max_decode_ms: u64,
    pub max_decoder_memory_bytes: u64,
}

impl Candidate {
    pub fn total_bytes(self) -> Option<u64> {
        self.payload_bytes.checked_add(self.metadata_bytes)
    }
}

fn admissible(candidate: Candidate, limits: Limits) -> bool {
    candidate.total_bytes().is_some()
        && candidate.encode_ms <= limits.max_encode_ms
        && candidate.decode_ms <= limits.max_decode_ms
        && candidate.decoder_memory_bytes <= limits.max_decoder_memory_bytes
}

/// Rank already-measured codecs within hard limits. Returns none if all violate limits.
/// `Balanced` uses dimensionless normalized time and size costs.
pub fn choose(
    profile: Profile,
    candidates: &[Candidate],
    limits: Limits,
    input_bytes: u64,
) -> Option<Candidate> {
    candidates
        .iter()
        .copied()
        .filter(|&c| admissible(c, limits))
        .min_by(|&a, &b| {
            let size_a = a.total_bytes().unwrap_or(u64::MAX);
            let size_b = b.total_bytes().unwrap_or(u64::MAX);
            match profile {
                Profile::Fast => {
                    (a.encode_ms, size_a, a.decode_ms, a.codec.tie_rank()).cmp(&(b.encode_ms, size_b, b.decode_ms, b.codec.tie_rank()))
                }
                Profile::Maximum => {
                    (size_a, a.encode_ms, a.decode_ms, a.codec.tie_rank()).cmp(&(size_b, b.encode_ms, b.decode_ms, b.codec.tie_rank()))
                }
                Profile::Balanced => {
                    let denominator_bytes = input_bytes.max(1) as f64;
                    let denominator_ms = limits.max_encode_ms.max(1) as f64;
                    let score = |c: Candidate| {
                        c.total_bytes().unwrap_or(u64::MAX) as f64 / denominator_bytes
                            + c.encode_ms as f64 / denominator_ms
                    };
                    score(a)
                        .total_cmp(&score(b))
                        .then_with(|| size_a.cmp(&size_b))
                        .then_with(|| a.encode_ms.cmp(&b.encode_ms))
                        .then_with(|| a.decode_ms.cmp(&b.decode_ms))
                        .then_with(|| a.codec.tie_rank().cmp(&b.codec.tie_rank()))
                }
            }
        })
}

#[cfg(test)]
mod tests {
    use super::*;

    const LIMIT: Limits = Limits {
        max_encode_ms: 1000,
        max_decode_ms: 1000,
        max_decoder_memory_bytes: 1024 * 1024 * 1024,
    };

    fn c(codec: Codec, bytes: u64, ms: u64) -> Candidate {
        Candidate {
            codec,
            payload_bytes: bytes,
            metadata_bytes: 4,
            encode_ms: ms,
            decode_ms: 1,
            decoder_memory_bytes: 1000,
        }
    }

    #[test]
    fn fast_vs_maximum() {
        let candidates = [c(Codec::Store, 1000, 1), c(Codec::Zstd, 300, 15)];
        assert_eq!(
            choose(Profile::Fast, &candidates, LIMIT, 1000)
                .unwrap()
                .codec,
            Codec::Store
        );
        assert_eq!(
            choose(Profile::Maximum, &candidates, LIMIT, 1000)
                .unwrap()
                .codec,
            Codec::Zstd
        );
    }

    #[test]
    fn memory_limit_rejects_codec() {
        let bad = Candidate {
            decoder_memory_bytes: u64::MAX,
            ..c(Codec::Lzma2, 1, 1)
        };
        let candidates = [bad, c(Codec::Store, 1024, 1)];
        assert_eq!(
            choose(Profile::Maximum, &candidates, LIMIT, 1024)
                .unwrap()
                .codec,
            Codec::Store
        );
    }

    #[test]
    fn stable_codec_tie_is_independent_of_candidate_order() {
        for profile in [Profile::Fast, Profile::Balanced, Profile::Maximum] {
            let zstd = c(Codec::Zstd, 400, 5);
            let store = c(Codec::Store, 400, 5);
            let left = choose(profile, &[zstd, store], LIMIT, 500).unwrap();
            let right = choose(profile, &[store, zstd], LIMIT, 500).unwrap();
            assert_eq!(left.codec, Codec::Store);
            assert_eq!(right.codec, Codec::Store);
        }
    }

    #[test]
    fn balanced_equal_score_prefers_lower_decode_cost() {
        let fast_decoder = Candidate {
            decode_ms: 2,
            ..c(Codec::Zstd, 400, 5)
        };
        let slow_decoder = Candidate {
            decode_ms: 30,
            ..c(Codec::Store, 400, 5)
        };
        for candidates in [
            [fast_decoder, slow_decoder],
            [slow_decoder, fast_decoder],
        ] {
            assert_eq!(
                choose(Profile::Balanced, &candidates, LIMIT, 500)
                    .unwrap()
                    .codec,
                Codec::Zstd
            );
        }
    }

    #[test]
    fn overflow_rejected() {
        let bad = Candidate {
            payload_bytes: u64::MAX,
            metadata_bytes: 1,
            ..c(Codec::Bzip3, 1, 1)
        };
        assert!(choose(Profile::Maximum, &[bad], LIMIT, 100).is_none());
    }
}
