#!/usr/bin/env python3
"""Explicitly fetch the separately maintained openly licensed evaluation portraits."""
import hashlib
from pathlib import Path
import sys
import subprocess

FILES = (
    ("collins-1.png", "https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.2/skimage/data/astronaut.png", "88431cd9653ccd539741b555fb0a46b61558b301d4110412b5bc28b5e3ea6cb5"),
    ("collins-2.jpg", "https://commons.wikimedia.org/wiki/Special:FilePath/Eileen%20Collins%2C%20early%20NASA%20portrait.jpg?width=600", "4a44110fc5edd1c8cab491f02fc85964350727b6a67e66ffd59a6ede6e4814be"),
    ("jemison-1.jpg", "https://commons.wikimedia.org/wiki/Special:FilePath/Mae%20Jemison%20-%20Official%20portrait%20of%201987%20astronaut%20candidate.jpg?width=600", "620342c6bc8c0988fb68f5d16dbbad7a6f5939de26d17c16f9585733db3ee904"),
    ("jemison-2.jpg", "https://commons.wikimedia.org/wiki/Special:FilePath/Dr.%20Mae%20C.%20Jemison%2C%20First%20African-American%20Woman%20in%20Space%20-%20Flickr%20-%20NASA%20on%20The%20Commons.jpg?width=600", "d9c65f7002c478ac6574a7cbde5df58192f8a5f9cf16b6d03c6db4e310edd2ff"),
    ("ride-1.jpg", "https://commons.wikimedia.org/wiki/Special:FilePath/Sally%20Ride%20in%201984.jpg?width=600", "75ae1b79f32c6e979b6e9dff80cd3f5bcf5c1295e93dd97ae7f422eb959d7770"),
    ("ride-2.jpg", "https://commons.wikimedia.org/wiki/Special:FilePath/DrSallyRide.jpg?width=600", "43cf03e297e1b3fffaf971172812dbbfee1a062698ae11a873faa7b2629d03c9"),
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
