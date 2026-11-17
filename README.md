# a-facegroup

A local, Apple-native command-line tool for discovering face clusters in image directories and previewing or exporting photos by cluster. It uses MediaIntelligence on macOS 27 or later; Swift 6 and the macOS 27 SDK are required to build. Clusters are algorithmic groupings, not verified identities. Entity IDs may change after regrouping; folder names encode the current native IDs and are not permanent names.

## Install

```sh
swift build -c release
cp .build/release/a-facegroup /usr/local/bin/a-facegroup
```

## Use

```sh
a-facegroup scan ~/Pictures/Unsorted --json
a-facegroup scan ~/Pictures/Unsorted --force
a-facegroup people list --json
a-facegroup people photos '<entity-id>'
a-facegroup identify ~/Pictures/NewPhoto.heic --json
a-facegroup export ~/Pictures/Sorted --json
a-facegroup export ~/Pictures/Sorted --mode copy --apply
# Alternatively: --mode symlink --apply
```

Scanning is recursive by default (`--recursive` is accepted) and skips symlinks, including symlinked directories. JPEG, PNG and HEIC files are considered. Unsupported or corrupt files are reported as failures and scanning continues; the command exits nonzero if any fail. An unchanged path is skipped based on size and modification time; `--force` rechecks it. Moves and renames are treated as new assets. Partial scans never delete old assets. Images with no detected faces go to `No_Faces`; identification reports unmatched faces separately. A group photo can appear in multiple folders.

`--json` writes structured snake_case JSON to stdout, including when `--quiet` is set. Without JSON, `--quiet` suppresses results. Errors go to stderr. For example, identification may return:

```json
{"faces": [{"entity_id": "native-id", "matched": true}, {"matched": false}], "total_faces": 2}
```

Export defaults to a preview. `--apply` creates copies or symbolic links and never intentionally overwrites existing paths; filename collisions receive numeric suffixes. Existing destination contents can therefore change a later preview. Source and destination directories may not overlap. Export refuses missing or changed indexed photos; restore them or rescan first. An interrupted export can leave already-created files in place; rerunning generates new collision-free names. Symbolic links refer to the original files and break if those files move.

## Data and privacy

The analyzer's private working directory and the application manifest are stored in `~/Library/Application Support/a-facegroup/`. Set `AFACEGROUP_HOME` to use a different library directory. A lock prevents concurrent commands from accessing the same library. The manifest contains canonical image paths, metadata, IDs and face counts; the analyzer owns its own storage. Protect and back up this sensitive local directory as appropriate. Processing is on-device; this application makes no network requests. Identification does not insert the image into the gallery, although opening a library and stale grouping may involve framework storage operations.

## Development

```sh
swift build
swift test
```

A native end-to-end smoke test on macOS 27 used a public-domain NASA portrait to check detection, regrouping, persistence, identification, and export. To repeat it with a licensed face portrait, run `python3 Tests/Integration/cli_smoke.py .build/debug/a-facegroup /path/to/portrait.png`. A second test checks unmatched faces and multi-person export: `python3 Tests/Integration/multiple_faces.py .build/debug/a-facegroup /path/to/two-person-image.png`. The tests require compatible, licensed images and a macOS 27 runtime; they do not measure recognition accuracy, throughput, or peak memory. GitHub Actions compiles the executable and tests with Xcode 27; a macOS 27 host is required to run them. In the restricted sandbox, the Vision model failed to load and MediaIntelligence crashed; the scan succeeded outside it. See [architecture](docs/architecture.md), [small labeled evaluation](docs/evaluation.md), and [implementation plan](docs/plan.md).

Inspired by the UNIX philosophy and Arthur-Ficial's Apple-native CLI projects, including apfel and auge. a-facegroup is an independent open-source project and is not officially affiliated with those projects. MIT licensed.

## Release preparation

Build and test with the macOS 27 SDK on a macOS 27 host, including both native smoke tests with appropriately licensed images. Run `swift build -c release` and verify `.build/release/a-facegroup --version` and `--help`; review the changelog, license, and documented validation limits before tagging `v0.1.0` and publishing release notes. Do not claim accuracy or runtime coverage beyond the tests actually performed.
