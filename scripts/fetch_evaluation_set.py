#!/usr/bin/env python3
"""Explicitly fetch the separately maintained openly licensed evaluation portraits."""
import argparse
import hashlib
from pathlib import Path
import subprocess
from urllib.parse import quote

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
CELEBRITIES = (
    ("reeves-1.jpg", "Keanu Reeves 2013 TIFF (cropped).jpg", "eb95faf1c9902538ec9ebc39579045d2e5373813414535b38afd56ac9d226ff6"),
    ("reeves-2.jpg", "Keanu Reeves SDCC 2024 1.jpg", "47a3b42bb252c8987439707e9d97777c9d3ca64d9f8754e9ebe93d504b72954b"),
    ("johnson-1.jpg", "Dwayne The Rock Johnson 2009 portrait.jpg", "b03f0e47bccc068facfe5a0373367017174836544a3f1835b6454c64946c0407"),
    ("johnson-2.jpg", "Dwayne Johnson 2018.jpg", "e27a26378af5ee270ba3558c48c16d4fddab360cb697c11812df4ff7753a2da8"),
    ("swift-1.jpg", "Taylor Swift (6820713278).jpg", "67a779e477da93c694bac53fa6eb2f00aac77d454f687cbace1cd6d65deea813"),
    ("swift-2.jpg", "Taylor Swift (52792258594).jpg", "67455a5a8657f3c32f371f8eceb48e67100a3c146bb7deb1e47be254287da758"),
    ("beyonce-1.jpg", "Beyonce - The Formation World Tour, at Wembley Stadium in London, England.jpg", "afe99713f12e2d1ff8cfbf78ed51f900925b5a099f7baba8789727e75ed1d1cc"),
    ("beyonce-2.jpg", 'Beyoncé performing "America Has a Problem" - Tottenham Hotspur Stadium - 1st June 2023 (100 of 118) (52945300587) (cropped).jpg', "f06ccb959b7fe0044a9c40aa2848c35acbc5c5e93c5d1d471ee24c298dadd7d5"),
)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("destination", type=Path, help="new output directory")
parser.add_argument("--include-celebrities", action="store_true", help="also fetch the separately attributed public-figure photos")
args = parser.parse_args()
destination = args.destination
files = FILES
if args.include_celebrities:
    files += tuple((name, "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(title) + "?width=1280", checksum) for name, title, checksum in CELEBRITIES)
# Require a new directory so existing user files are never overwritten.
destination.mkdir(parents=True, exist_ok=False)
for name, url, expected in files:
    data = subprocess.run(["/usr/bin/curl", "--fail", "--silent", "--show-error", "--location", "--max-time", "30", "--user-agent", "a-facegroup evaluation fixture fetcher", url], check=True, stdout=subprocess.PIPE).stdout
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum mismatch for {name}; downloaded bytes were not written. See docs/evaluation.md.")
    with (destination / name).open("xb") as output:
        output.write(data)
    print(name, actual)
