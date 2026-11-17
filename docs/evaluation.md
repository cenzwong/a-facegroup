# Small labeled evaluation

This is a reproducible starting set, separate from the repository and from the integration fixtures. The labels below are based on the source descriptions and each image contains one visible subject. The images are not bundled. NASA imagery has separate restrictions on insignia and endorsement; check each source before reuse. The sources describe these photographs as public domain in the United States, except the 1992 Jemison photo, which is marked no known copyright restrictions by Flickr Commons.

| Local filename | Subject | Source | SHA-256 of tested file |
| --- | --- | --- | --- |
| `collins-1.png` | Eileen Collins | [scikit-image astronaut](https://scikit-image.org/docs/0.25.x/api/skimage.data.html#skimage.data.astronaut) | `88431cd9653ccd539741b555fb0a46b61558b301d4110412b5bc28b5e3ea6cb5` |
| `collins-2.jpg` | Eileen Collins | [early NASA portrait](https://commons.wikimedia.org/wiki/File:Eileen_Collins,_early_NASA_portrait.jpg) | `4a44110fc5edd1c8cab491f02fc85964350727b6a67e66ffd59a6ede6e4814be` |
| `jemison-1.jpg` | Mae Jemison | [1987 portrait](https://commons.wikimedia.org/wiki/File:Mae_Jemison_-_Official_portrait_of_1987_astronaut_candidate.jpg) | `620342c6bc8c0988fb68f5d16dbbad7a6f5939de26d17c16f9585733db3ee904` |
| `jemison-2.jpg` | Mae Jemison | [1992 portrait](https://commons.wikimedia.org/wiki/File:Dr._Mae_C._Jemison,_First_African-American_Woman_in_Space_-_Flickr_-_NASA_on_The_Commons.jpg) | `d9c65f7002c478ac6574a7cbde5df58192f8a5f9cf16b6d03c6db4e310edd2ff` |
| `ride-1.jpg` | Sally Ride | [1984 portrait](https://commons.wikimedia.org/wiki/File:Sally_Ride_in_1984.jpg) | `75ae1b79f32c6e979b6e9dff80cd3f5bcf5c1295e93dd97ae7f422eb959d7770` |
| `ride-2.jpg` | Sally Ride | [later portrait](https://commons.wikimedia.org/wiki/File:DrSallyRide.jpg) | `43cf03e297e1b3fffaf971172812dbbfee1a062698ae11a873faa7b2629d03c9` |
| `shepard-1.jpg` | Alan Shepard | [1960 portrait](https://commons.wikimedia.org/wiki/File:Alan_Shepard_in_1960.jpg) | `3f8ef484565605683cfe5b4aec510c165afafbfe00477899faecfb521a097488` |
| `shepard-2.jpg` | Alan Shepard | [1962 portrait](https://commons.wikimedia.org/wiki/File:Alan_Shepard_1962_NASA_portrait.jpg) | `53d716f08d301b30894a6c1a00ffa1f21a6c6af03a9a4121b073f8c354ad75e0` |

The Commons files were downloaded through `Special:FilePath` with `?width=600`; output dimensions vary. Verify hashes because downloads or resizing may change. Keep the collection and labels in user-controlled storage. To fetch the exact tested bytes into a new directory, explicitly run `python3 scripts/fetch_evaluation_set.py /path/to/new-evaluation-directory`. This separate development script makes network requests, verifies each SHA-256, and refuses an existing destination; the CLI itself does not use it. If a source changes or a download fails, the newly created directory may contain a partial set.

## Observed run

On 2026-11-17, macOS 27.0.1 on Apple Silicon, a release build scanned the four photos into a fresh library outside the restricted sandbox. `people list --json` returned two clusters: both Collins photos in one and both Shepard photos in the other. For these four labeled images, this observed zero false merges and zero false splits. Scan reported four processed, no failures, and no no-face images. A separate held-out check indexed only `collins-1.png`: `collins-2.jpg` matched that entity and `shepard-1.jpg` was unmatched. Neither held-out photo was inserted. This is one known and one unknown example, not an unmatched-rate measurement. Repeat with `python3 Tests/Integration/heldout_identification.py /path/to/a-facegroup /path/to/collins-1.png /path/to/collins-2.jpg /path/to/shepard-1.jpg`. An optional fifth argument can supply a two-face image containing the indexed subject and the unknown subject; a temporary composite of the Collins and Shepard portraits produced one match and one unmatched face.

`/usr/bin/time -l` reported 0.36 seconds elapsed (about 11.1 images/second) and 58,507,264 bytes maximum resident set size for the CLI process. These figures are a single warm-machine observation, not a benchmark: the set is tiny, startup and caching dominate, and the process measurement does not account for separate system services or total system memory. They do not establish throughput or peak memory for large collections.

To repeat, use a fresh library and compare the paths in each returned cluster with the table above:

```sh
AFACEGROUP_HOME=/path/to/new-library /usr/bin/time -l a-facegroup scan /path/to/labeled-photos --json
AFACEGROUP_HOME=/path/to/new-library a-facegroup people list --json
```

For a separately maintained set of single-person photos, label each canonical path with its known person in a JSON array, for example:

```json
[{"path": "/absolute/path/photo-a.jpg", "person": "person-a"}, {"path": "/absolute/path/photo-b.jpg", "person": "person-a"}]
```

Use a fresh library containing only those labeled photos, save `a-facegroup people list --json` to a file, then run `python3 scripts/evaluate_clusters.py labels.json people.json`. This offline tool counts false merge and split **pairs** among assigned photos and reports unassigned photos separately. It rejects unlabeled returned photos and photos in multiple clusters; it is not suitable for group photos or face-level ground truth. An unassigned photo may have failed, contain no detected face, or be otherwise absent; it is not the same as an unmatched face from `identify`. Assess identification separately with held-out images and report the dataset selection and known limits. `/usr/bin/time -l` measures the CLI process, not total system-service memory.

This set is far too small and homogeneous to estimate real-world recognition accuracy. A representative, consented or appropriately licensed collection with varied people, poses, lighting, group photos, and unseen identification images is still needed; report its merges, splits, unmatched faces, throughput, and memory separately.

## Expanded labeled check

On the same macOS 27.0.1 host, the release CLI scanned all eight photos in a fresh library. Labels were checked against source descriptions and the images inspected for one visible subject each. The offline evaluator reported eight assigned photos, four clusters, zero unassigned photos, zero false-merge pairs, and zero false-split pairs. `/usr/bin/time -l` reported 0.50 seconds and 63,946,752 bytes peak CLI RSS (excluding separate system services). Four separate held-out checks each indexed the first portrait for one subject, identified their second portrait, and identified another subject’s second portrait. Each known face matched and each unknown face was unmatched. Repeat with `python3 Tests/Integration/expanded_identification.py /path/to/a-facegroup /path/to/eight-photo-set`. This remains a very small, selected collection of official portraits; it is not representative of a diverse real-world library, and the timing is a single observation.

## Public-figure evaluation

A separate 16-photo set combined the eight NASA portraits above with two photos each of Beyoncé, Dwayne Johnson, Keanu Reeves, and Taylor Swift. The additional photos were selected from Wikimedia Commons, checked against source descriptions, and visually reviewed for one identifiable main subject. They include stage and event images, occlusion, and changes across years. All were downloaded through Commons with `?width=1280`; some were already cropped at the source, and Commons returned resized images where available. They are not bundled. Copyright licenses do not by themselves resolve personality or privacy rights; review each source and applicable terms before reuse. This public-figure convenience sample is still small and selected, and is not representative of a general population or a typical private photo library.

| File | Source and attribution | License | SHA-256 of tested bytes |
| --- | --- | --- | --- |
| `beyonce-1.jpg` | [Formation World Tour crop](<https://commons.wikimedia.org/wiki/File:Beyonce_-_The_Formation_World_Tour,_at_Wembley_Stadium_in_London,_England.jpg>), Rocbeyonce | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | `afe99713f12e2d1ff8cfbf78ed51f900925b5a099f7baba8789727e75ed1d1cc` |
| `beyonce-2.jpg` | [Renaissance World Tour crop](<https://commons.wikimedia.org/wiki/File:Beyonc%C3%A9_performing_%22America_Has_a_Problem%22_-_Tottenham_Hotspur_Stadium_-_1st_June_2023_(100_of_118)_(52945300587)_(cropped).jpg>), Raph_PH; source crop by BeyPolite | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) | `f06ccb959b7fe0044a9c40aa2848c35acbc5c5e93c5d1d471ee24c298dadd7d5` |
| `johnson-1.jpg` | [2009 portrait](https://commons.wikimedia.org/wiki/File:Dwayne_The_Rock_Johnson_2009_portrait.jpg), David Shankbone | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) | `b03f0e47bccc068facfe5a0373367017174836544a3f1835b6454c64946c0407` |
| `johnson-2.jpg` | [2018 interview](https://commons.wikimedia.org/wiki/File:Dwayne_Johnson_2018.jpg), MTV International | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) | `e27a26378af5ee270ba3558c48c16d4fddab360cb697c11812df4ff7753a2da8` |
| `reeves-1.jpg` | [2013 TIFF crop](<https://commons.wikimedia.org/wiki/File:Keanu_Reeves_2013_TIFF_(cropped).jpg>), GabboT | [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/) | `eb95faf1c9902538ec9ebc39579045d2e5373813414535b38afd56ac9d226ff6` |
| `reeves-2.jpg` | [2024 Comic-Con](https://commons.wikimedia.org/wiki/File:Keanu_Reeves_SDCC_2024_1.jpg), Chris Roth | [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/) | `47a3b42bb252c8987439707e9d97777c9d3ca64d9f8754e9ebe93d504b72954b` |
| `swift-1.jpg` | [2012 performance](<https://commons.wikimedia.org/wiki/File:Taylor_Swift_(6820713278).jpg>), Eva Rinaldi | [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/) | `67a779e477da93c694bac53fa6eb2f00aac77d454f687cbace1cd6d65deea813` |
| `swift-2.jpg` | [2023 performance](<https://commons.wikimedia.org/wiki/File:Taylor_Swift_(52792258594).jpg>), Ronald Woan | [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/) | `67455a5a8657f3c32f371f8eceb48e67100a3c146bb7deb1e47be254287da758` |

On macOS 27.0.1 with the release build at commit `7c4c486`, all 16 images were processed and assigned to 11 clusters. The offline pairwise scorer reported **zero false merge pairs and three false split pairs**, with zero unassigned photos. The split pairs were the Beyoncé, Reeves, and Swift pairs. This scores photo-to-cluster assignments using the labels; it does not validate detected face bounding boxes or establish demographic accuracy. A repeat using independently downloaded checksum-verified bytes returned the same pair counts.

For held-out identification, each of eight separate galleries contained the first photo of one subject. The second photo was the known query, and the next subject's second photo was the unknown query. Five known faces matched and three were unmatched; all eight unknown faces were unmatched. No gallery had zero or multiple detected faces in this run. These 16 queries and the clustering run are too few to estimate error rates.

The current-head clustering run took 1.19 seconds and peaked at 71,843,840 bytes CLI-process RSS according to `/usr/bin/time -l`; this excludes separately running system services, so total system memory is not measured. It is a single small run, not a throughput or memory benchmark. During repeated held-out runs on this host, two of seven runs failed; one captured failure was reported by Apple's Core Data stack as SQLite `SQLITE_IOERR_VNODE` (6922). No cause was established. Five runs passed; the evaluation tool reports command failures rather than silently retrying them.

To fetch the full set explicitly, run `python3 scripts/fetch_evaluation_set.py --include-celebrities /path/to/new-directory`. This development-only script uses the network and checks hashes; the CLI does not. Create a labels JSON array with the documented absolute paths and person identifiers, scan that directory into a fresh library, and run `scripts/evaluate_clusters.py` as above. `python3 scripts/evaluate_identification.py /path/to/a-facegroup labels.json /path/to/existing-scratch-directory` runs the held-out method locally using temporary galleries. The dataset is not committed, and an interrupted fetch can leave a partial new directory.

## Synthetic scale check

On the same host, a release build scanned 1,000 distinct paths containing identical one-pixel PNGs into a fresh library, then scanned the directory again. The first run reported 1,000 processed and 1,000 no-face images in 8.04 seconds; the second reported 1,000 skipped and zero processed in 0.22 seconds. `/usr/bin/time -l` reported CLI-process maximum resident set sizes of 42,008,576 and 20,922,368 bytes respectively. Each result is one run and excludes any memory in separate system services. These tiny identical images exercise traversal, persistence and skip behavior; they are not representative of full-resolution photos, facial inference, clustering accuracy, or production throughput.

## Repeated-portrait scale check (before ingestion lifetime fix)

On the same host and release build, 1,000 unique paths were created as hard links to the four labeled portraits above (250 paths per image). A fresh scan processed all 1,000 with no reported failures or no-face images, and produced two clusters of 500 faces each. A subsequent scan skipped all 1,000. `/usr/bin/time -l` reported 45.68 seconds and 934,166,528 bytes maximum resident set size for the first CLI process, and 0.25 seconds and 21,250,048 bytes for the repeat. This single run excludes separate system-service memory and uses only two identities and four source images; it is a load check, not a representative accuracy or performance estimate. The high first-run process memory prompted the follow-up investigation below.

The paths were hard links, not 1,000 distinct photographic inputs. On a filesystem that supports hard links, this Python fragment creates the test inputs from a directory containing exactly the four labeled images:

```python
from pathlib import Path
import os
source = Path('/path/to/four-selected-labeled-images')
destination = Path('/path/to/empty-test-directory')
photos = sorted(source.iterdir())
for n in range(1000):
    image = photos[n % len(photos)]
    os.link(image, destination / f'{n:04d}{image.suffix}')
```

Use a fresh library, time a scan and a repeat with the commands above, then inspect `people list --json`. Do not generalize results from duplicate portraits to real-world collections.

A follow-up sampled CLI RSS every 0.5 seconds while the same 1,000-path fixture was scanned into another fresh library. The maximum sampled RSS was 1,291,728 KiB; the largest sampled values in successive 0–249, 250–499, 500–749, and 750–999 recorded-asset ranges were 438,384, 824,512, 1,207,616, and 1,291,728 KiB. The increasing samples occurred during ingestion, before the final grouping call. Sampling can miss the actual peak, and this does not identify which component retained memory.

An isolated, uncommitted experiment reopened the analyzer after every 50 processed assets. It completed with the same cluster counts but reached 1,609,248 KiB sampled RSS. These are single sequential runs with uncontrolled cache and system conditions, so they do not establish a comparative benchmark; reopening did not demonstrate a memory improvement and is not used by the CLI. Profiling on a representative collection is still needed to understand memory growth.

## Per-image task lifetime change

An isolated experiment awaited a separate task for each image ingestion, allowing each task's framework buffers to be released before the next image. On the same repeated-portrait fixture, 0.5-second RSS sampling showed a maximum of 80,128 KiB, compared with 1,291,728 KiB for the earlier sampled run. The CLI now uses that per-image task lifetime.

A subsequent run of the release build with that change processed all 1,000 paths, returned two clusters of 500 faces, and skipped all 1,000 on repeat. `/usr/bin/time -l` reported 45.75 seconds and 126,074,880 bytes maximum CLI RSS for the first scan. These sequential runs used the same host and fixture but did not control cache or other system activity. They are evidence of substantially lower process memory on this fixture, not a guarantee for other images, total system memory, or larger collections.

After switching to structured child tasks to propagate cancellation, another 1,000-path run returned the same two 500-face clusters and skipped all paths on repeat. `/usr/bin/time -l` reported 45.33 seconds and 128,385,024 bytes maximum CLI RSS. As above, this is a single run on repeated portraits and excludes memory in separate system services.
