use std::env;
use std::fs::File;
use std::io::{Read, Write};
use std::path::PathBuf;

fn main() -> Result<(), std::io::Error> {
    // Generate
    // ${CARGO_TARGET_DIR}/${PROFILE}/pep_engine_sequoia_backend.pc from
    // ${SRC}/pep_engine_sequoia_backend.pc.in.

    // Location of pep_engine_sequoia_backend.pc.in.
    let src = env::current_dir()?;
    let mut pc_in = PathBuf::from(&src);
    pc_in.push("pep_engine_sequoia_backend.pc.in");

    // Location of the build directory (e.g.,
    // `/tmp/pep_engine_sequoia_backend/debug`).
    let mut build_dir = PathBuf::from(&src);
    if let Some(target_dir) = env::var_os("CARGO_TARGET_DIR") {
        // If CARGO_TARGET_DIR is absolute, this will first clear pc.
        build_dir.push(target_dir);
    } else {
        build_dir.push("target");
    }
    let profile = env::var_os("PROFILE")
        .expect("PROFILE not set");
    build_dir.push(&profile);

    // Location of pep_engine_sequoia_backend.pc.
    let mut pc = build_dir.clone();
    pc.push("pep_engine_sequoia_backend.pc");

    // Read the .pc.in file, do the substitutions, and generate the
    // .pc file.
    let mut pc_in = File::open(pc_in)?;
    let mut content = Vec::new();
    pc_in.read_to_end(&mut content)?;

    // This is set to allow the use of the library from the build
    // directory.
    let content = String::from_utf8(content).unwrap()
        .replace("LIBDIR",
                 &build_dir
                     .to_str()
                     .expect("build directory is not UTF-8 encoded"))
        .replace("VERSION",
                 &env::var_os("CARGO_PKG_VERSION")
                     .expect("CARGO_PKG_VERSION not set")
                     .into_string()
                     .expect("CARGO_PKG_VERSION is not UTF-8 encoded"));

    let mut pc = File::create(&pc).expect(
        &format!("Creating {:?} (CARGO_TARGET_DIR: {:?})",
                 pc, env::var_os("CARGO_TARGET_DIR")));
    pc.write_all(content.as_bytes())?;

    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=pep_engine_sequoia_backend.pc.in");
    println!(r"cargo:rustc-link-search=~/src/botan");


    eprintln!("Generated {:?} with:\n{}\nEOF", pc, content);

    Ok(())
}
