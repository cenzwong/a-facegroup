# Small labeled evaluation

This is a reproducible starting set, separate from the repository and from the integration fixtures. The labels below are based on the source descriptions and each image contains one visible subject. The images are not bundled. NASA imagery has separate restrictions on insignia and endorsement; check each source before reuse. Each listed source describes the photograph as public domain in the United States.

| Local filename | Subject | Source | SHA-256 of tested file |
| --- | --- | --- | --- |
| `collins-1.png` | Eileen Collins | [scikit-image astronaut](https://scikit-image.org/docs/0.25.x/api/skimage.data.html#skimage.data.astronaut) | `88431cd9653ccd539741b555fb0a46b61558b301d4110412b5bc28b5e3ea6cb5` |
| `collins-2.jpg` | Eileen Collins | [early NASA portrait](https://commons.wikimedia.org/wiki/File:Eileen_Collins,_early_NASA_portrait.jpg) | `4a44110fc5edd1c8cab491f02fc85964350727b6a67e66ffd59a6ede6e4814be` |
| `shepard-1.jpg` | Alan Shepard | [1960 portrait](https://commons.wikimedia.org/wiki/File:Alan_Shepard_in_1960.jpg) | `3f8ef484565605683cfe5b4aec510c165afafbfe00477899faecfb521a097488` |
| `shepard-2.jpg` | Alan Shepard | [1962 portrait](https://commons.wikimedia.org/wiki/File:Alan_Shepard_1962_NASA_portrait.jpg) | `53d716f08d301b30894a6c1a00ffa1f21a6c6af03a9a4121b073f8c354ad75e0` |

The tested Commons files were downloaded through `Special:FilePath` with `?width=600`; the service returned 960-pixel-wide JPEGs. Verify hashes because downloads or resizing may change. Keep the collection and labels in user-controlled storage.

## Observed run

On 2026-11-17, macOS 27.0.1 on Apple Silicon, a release build scanned the four photos into a fresh library outside the restricted sandbox. `people list --json` returned two clusters: both Collins photos in one and both Shepard photos in the other. For these four labeled images, this observed zero false merges and zero false splits. Scan reported four processed, no failures, and no no-face images. A separate held-out check indexed only `collins-1.png`: `collins-2.jpg` matched that entity and `shepard-1.jpg` was unmatched. Neither held-out photo was inserted. This is one known and one unknown example, not an unmatched-rate measurement. Repeat with `python3 Tests/Integration/heldout_identification.py /path/to/a-facegroup /path/to/collins-1.png /path/to/collins-2.jpg /path/to/shepard-1.jpg`.

`/usr/bin/time -l` reported 0.36 seconds elapsed (about 11.1 images/second) and 58,507,264 bytes maximum resident set size for the CLI process. These figures are a single warm-machine observation, not a benchmark: the set is tiny, startup and caching dominate, and the process measurement does not account for separate system services or total system memory. They do not establish throughput or peak memory for large collections.

To repeat, use a fresh library and compare the paths in each returned cluster with the table above:

```sh
AFACEGROUP_HOME=/path/to/new-library /usr/bin/time -l a-facegroup scan /path/to/labeled-photos --json
AFACEGROUP_HOME=/path/to/new-library a-facegroup people list --json
```

This set is far too small and homogeneous to estimate real-world recognition accuracy. A representative, consented or appropriately licensed collection with varied people, poses, lighting, group photos, and unseen identification images is still needed; report its merges, splits, unmatched faces, throughput, and memory separately.

## Synthetic scale check

On the same host, a release build scanned 1,000 distinct paths containing identical one-pixel PNGs into a fresh library, then scanned the directory again. The first run reported 1,000 processed and 1,000 no-face images in 8.04 seconds; the second reported 1,000 skipped and zero processed in 0.22 seconds. `/usr/bin/time -l` reported CLI-process maximum resident set sizes of 42,008,576 and 20,922,368 bytes respectively. Each result is one run and excludes any memory in separate system services. These tiny identical images exercise traversal, persistence and skip behavior; they are not representative of full-resolution photos, facial inference, clustering accuracy, or production throughput.

## Repeated-portrait scale check

On the same host and release build, 1,000 unique paths were created as hard links to the four labeled portraits above (250 paths per image). A fresh scan processed all 1,000 with no reported failures or no-face images, and produced two clusters of 500 faces each. A subsequent scan skipped all 1,000. `/usr/bin/time -l` reported 45.68 seconds and 934,166,528 bytes maximum resident set size for the first CLI process, and 0.25 seconds and 21,250,048 bytes for the repeat. This single run excludes separate system-service memory and uses only two identities and four source images; it is a load check, not a representative accuracy or performance estimate. The high first-run process memory is relevant when sizing larger jobs and has not been profiled further.

The paths were hard links, not 1,000 distinct photographic inputs. On a filesystem that supports hard links, this Python fragment creates the test inputs from a directory containing exactly the four labeled images:

```python
from pathlib import Path
import os
source = Path('/path/to/four-labeled-images')
destination = Path('/path/to/empty-test-directory')
photos = sorted(source.iterdir())
for n in range(1000):
    image = photos[n % len(photos)]
    os.link(image, destination / f'{n:04d}{image.suffix}')
```

Use a fresh library, time a scan and a repeat with the commands above, then inspect `people list --json`. Do not generalize results from duplicate portraits to real-world collections.

A follow-up sampled CLI RSS every 0.5 seconds while the same 1,000-path fixture was scanned into another fresh library. The maximum sampled RSS was 1,291,728 KiB; the largest sampled values in successive 0–249, 250–499, 500–749, and 750–999 recorded-asset ranges were 438,384, 824,512, 1,207,616, and 1,291,728 KiB. The increasing samples occurred during ingestion, before the final grouping call. Sampling can miss the actual peak, and this does not identify which component retained memory.

An isolated, uncommitted experiment reopened the analyzer after every 50 processed assets. It completed with the same cluster counts but reached 1,609,248 KiB sampled RSS. These are single sequential runs with uncontrolled cache and system conditions, so they do not establish a comparative benchmark; reopening did not demonstrate a memory improvement and is not used by the CLI. Profiling on a representative collection is still needed to understand memory growth.
