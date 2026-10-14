.PHONY: test rust-test py-test lint bench-smoke

test: py-test rust-test

py-test:
	python3 -m unittest discover -s tests -v

rust-test:
	cargo test --workspace

lint:
	cargo fmt --all -- --check
	cargo clippy --workspace --all-targets -- -D warnings

bench-smoke:
	python3 tools/make_corpus.py --output sample-corpus
	python3 tools/benchmark.py sample-corpus --output bench-results.json --repetitions 3
