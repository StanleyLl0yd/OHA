//! M0 research command. This deliberately does not create .oha archives.

use std::env;
use std::path::Path;
use std::process::ExitCode;

fn usage() {
    eprintln!("OHA 0.0.0 - M0 research scaffold (archive pack/extract not implemented)");
    eprintln!("Usage: oha-archiver analyze <file>");
}

fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() != 2 || args[0] != "analyze" {
        usage();
        return Err("invalid command or arguments".into());
    }
    let path = Path::new(&args[1]);
    let s = oha_analysis::analyze_file(path)
        .map_err(|error| format!("failed to analyze '{}': {error}", path.display()))?;
    println!("file: {}", path.display());
    println!("input_bytes: {}", s.input_bytes);
    println!("sampled_bytes: {}", s.sampled_bytes);
    println!("hint: {:?}", s.hint);
    println!("entropy_bits_per_byte: {:.4}", s.entropy_bits_per_byte);
    println!("printable_ascii_ratio: {:.4}", s.ascii_ratio);
    println!("zero_ratio: {:.4}", s.zero_ratio);
    println!("unique_byte_values: {}", s.unique_byte_values);
    println!("note: descriptive signal only; not an archive size prediction");
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(message) => {
            eprintln!("error: {message}");
            ExitCode::FAILURE
        }
    }
}
