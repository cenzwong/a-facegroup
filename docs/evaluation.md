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

On 2026-11-17, macOS 27.0.1 on Apple Silicon, a release build scanned the four photos into a fresh library outside the restricted sandbox. `people list --json` returned two clusters: both Collins photos in one and both Shepard photos in the other. For these four labeled images, this observed zero false merges and zero false splits. Scan reported four processed, no failures, and no no-face images. Unmatched identification was separately checked against an empty gallery in the integration test; no unmatched-rate measurement was made on this set.

`/usr/bin/time -l` reported 0.36 seconds elapsed (about 11.1 images/second) and 58,507,264 bytes maximum resident set size for the CLI process. These figures are a single warm-machine observation, not a benchmark: the set is tiny, startup and caching dominate, and the process measurement does not account for separate system services or total system memory. They do not establish throughput or peak memory for large collections.

To repeat, use a fresh library and compare the paths in each returned cluster with the table above:

```sh
AFACEGROUP_HOME=/path/to/new-library /usr/bin/time -l a-facegroup scan /path/to/labeled-photos --json
AFACEGROUP_HOME=/path/to/new-library a-facegroup people list --json
```

This set is far too small and homogeneous to estimate real-world recognition accuracy. A representative, consented or appropriately licensed collection with varied people, poses, lighting, group photos, and unseen identification images is still needed; report its merges, splits, unmatched faces, throughput, and memory separately.
