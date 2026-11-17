#!/usr/bin/env python3
"""Explicitly fetch the separately maintained public-domain evaluation portraits."""
import hashlib
from pathlib import Path
import sys
import subprocess

FILES = (
    ("collins-1.png", "https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.2/skimage/data/astronaut.png", "88431cd9653ccd539741b555fb0a46b61558b301d4110412b5bc28b5e3ea6cb5"),
    ("collins-2.jpg", "https://commons.wikimedia.org/wiki/Special:FilePath/Eileen%20Collins%2C%20early%20NASA%20portrait.jpg?width=600", "4a44110fc5edd1c8cab491f02fc85964350727b6a67e66ffd59a6ede6e4814be"),
    ("shepard-1.jpg", "https://commons.wikimedia.org/wiki/Special:FilePath/Alan%20Shepard%20in%201960.jpg?width=600", "3f8ef484565605683cfe5b4aec510c165afafbfe00477899faecfb521a097488"),
    ("shepard-2.jpg", "https://commons.wikimedia.org/wiki/Special:FilePath/Alan%20Shepard%201962%20NASA%20portrait.jpg?width=600", "53d716f08d301b30894a6c1a00ffa1f21a6c6af03a9a4121b073f8c354ad75e0"),
)
if len(sys.argv) != 2:
    raise SystemExit("Usage: python3 scripts/fetch_evaluation_set.py <new-output-directory>")
destination = Path(sys.argv[1])
# Require a new directory so existing user files are never overwritten.
destination.mkdir(parents=True, exist_ok=False)
for name, url, expected in FILES:
    data = subprocess.run(["/usr/bin/curl", "--fail", "--silent", "--show-error", "--location", "--max-time", "30", "--user-agent", "a-facegroup evaluation fixture fetcher", url], check=True, stdout=subprocess.PIPE).stdout
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum mismatch for {name}; downloaded bytes were not written. See docs/evaluation.md.")
    with (destination / name).open("xb") as output:
        output.write(data)
    print(name, actual)
