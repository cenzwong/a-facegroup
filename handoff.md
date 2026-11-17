# Engineering Handoff — a-facegroup

**Project:** `a-facegroup`  
**Repository:** `cenzwong/a-facegroup` (new repository)  
**CLI executable:** `a-facegroup`  
**Language:** Swift 6  
**Platform:** macOS 27+  
**Framework:** Apple MediaIntelligence  
**License:** MIT  
**Status:** New project — v0.1.0 MVP

---

## 1. Project Objective

Build `a-facegroup`, an independent, lightweight, Apple-native command-line application that exposes Apple's `FaceGroupAnalyzer` API for local face clustering and photo organisation.

### Golden Goal

> Expose Apple's on-device FaceGroupAnalyzer as a privacy-first, composable UNIX CLI that discovers people across photo collections and enables safe, non-destructive organisation of photos by person.

The tool should allow users to point it at a directory containing thousands of unsorted photos, automatically group faces belonging to the same people, and optionally export the photos into person-specific directories.

No cloud services, user accounts, API keys, or third-party face recognition models should be required.

### Design Inspiration

Follow the engineering philosophy of:

- [Arthur-Ficial/auge](https://github.com/Arthur-Ficial/auge) — Apple's Vision framework exposed through a UNIX CLI.
- [Arthur-Ficial/apfel](https://github.com/Arthur-Ficial/apfel) — Apple-native, local-first tooling.
- [cenzwong/kern](https://github.com/cenzwong/kern) — Native Swift CLI with clean separation between application, service, and framework integration.

This is **an independent project**, not an AUGE fork or official extension of the apfel ecosystem.

Adopt useful engineering conventions, not unnecessary architectural complexity.

---

## 2. Core Design Principles

### 2.1 Apple-native

- Swift 6 with strict concurrency checking.
- Use `MediaIntelligence.FaceGroupAnalyzer` as the primary engine.
- Avoid Python, PyTorch, ONNX, InsightFace, and custom face clustering algorithms.
- Prefer Apple system frameworks and Swift standard libraries.
- Do not implement functionality already provided by `FaceGroupAnalyzer`.

### 2.2 Local-first and privacy-preserving

- All inference and image processing must remain on-device.
- No telemetry, analytics, or network requests.
- No uploads to external services.
- Face metadata and analysis state must remain in user-controlled local storage.
- Avoid logging sensitive face metadata or raw image contents.

### 2.3 UNIX philosophy

- A small, composable executable.
- Support structured, machine-readable output.
- JSON uses `snake_case` field names.
- Results go to stdout.
- Diagnostics and progress go to stderr.
- Nonzero exit codes for errors.
- Support `--json`, `--quiet`, `--help`, and `--version`.
- Never mix progress messages with JSON output.

### 2.4 Non-destructive

- Scanning never modifies source photos.
- Export operations must not modify or delete originals.
- Preview export changes by default.
- Explicit confirmation through `--apply` is required to write exported files.
- Never overwrite unrelated existing files silently.
- Validate source and destination paths to prevent recursive export.

### 2.5 Persistent and incremental

- Preserve the analyzer working directory between executions.
- Avoid reprocessing unchanged images.
- Use consistent, unique asset identifiers.
- Support adding photos without rebuilding the entire collection.
- Do not assume generated face cluster identifiers remain unchanged across regrouping or rebuilding.

### 2.6 Minimal, testable architecture

- Use protocols or dependency injection where they provide real testing value.
- Keep framework calls isolated from CLI parsing and file export.
- Prefer pure Swift unit tests for filesystem planning, path validation, manifest handling, and output formatting.
- Do not introduce abstract plugin architectures or generic backend frameworks prematurely.

---

## 3. Apple API Integration

### Official documentation

- [MediaIntelligence](https://developer.apple.com/documentation/mediaintelligence)
- [FaceGroupAnalyzer](https://developer.apple.com/documentation/mediaintelligence/facegroupanalyzer)
- [Detecting and grouping faces in images](https://developer.apple.com/documentation/mediaintelligence/detecting-and-grouping-faces-in-images)

Use these as authoritative sources.

Do not invent framework methods, types, properties, or compatibility guarantees.

### Supported workflow

**Step 1 — Initialise analyzer**

Create a persistent working directory and initialise:

`FaceGroupAnalyzer(workingDirectory:)`

**Step 2 — Insert images**

Create `MediaIntelligenceImageAsset` instances with unique, consistent IDs.

Call:

`insertOrUpdateAssets(_:)`

Consume its asynchronous results and record the discovered face information.

**Step 3 — Cluster faces**

Check `analyzer.state`.

When stale, call:

`update()`

**Step 4 — Retrieve people**

Use:

- `allEntities`
- `allFacesByEntityID`
- `allAssetIDsByEntityID`
- `fetchFaces(for:)`
- `fetchAssetIDs(for:)`

Choose the most appropriate API for each operation.

**Step 5 — Identify new images**

Use:

`identifyFaces(in:)`

This operation must not modify the stored gallery.

**Step 6 — Handle removal or reset**

Apple provides:

- `deleteAssets(_:)`
- `deleteAllAssets()`
- `purge(workingDirectory:)`

Do not expose destructive reset functionality during v0.1.0 unless necessary and protected by explicit confirmation.

### Important API constraints

- Requires the macOS 27 SDK and compatible runtime.
- The analyzer owns the internal contents of its working directory.
- Never directly modify or query Apple's private analyzer storage files.
- An entity represents a face cluster, not a verified real-world identity.
- Do not assume Apple exposes raw face embeddings, similarity scores, confidence thresholds, or manual cluster merge operations.
- Verify API behaviour by compiling and running on a compatible macOS environment.

---

## 4. Proposed CLI Interface

Use subcommands rather than a collection of unrelated flags.

### 4.1 Scan photos

```bash
a-facegroup scan ~/Pictures/Unsorted
```

Recursively discover supported image files, insert new or changed assets, and update face clusters.

Options:

```bash
a-facegroup scan ~/Pictures/Unsorted \
  --recursive \
  --json
```

Expected behaviour:

- Detect supported image formats.
- Process images in bounded batches.
- Skip unchanged assets using the local manifest.
- Report processed, skipped, and failed assets.
- Trigger clustering after ingestion.
- Preserve source files.
- Allow repeated execution without duplicating assets.

### 4.2 List discovered people

```bash
a-facegroup people list
```

JSON:

```bash
a-facegroup people list --json
```

Illustrative response:

```json
{
  "people": [
    {
      "id": "person_001",
      "face_count": 128,
      "photo_count": 93
    },
    {
      "id": "person_002",
      "face_count": 57,
      "photo_count": 42
    }
  ],
  "total_people": 2
}
```

`person_001` is an illustrative application-facing label. Do not assume Apple returns identifiers in this format.

Do not promise stable display labels unless an explicit mapping is implemented.

### 4.3 Retrieve photos belonging to a person

```bash
a-facegroup people photos <person-id>
```

Should return the corresponding photo paths.

Multiple people may reference the same photo.

### 4.4 Identify people in a new image

```bash
a-facegroup identify ~/Pictures/NewPhoto.heic
```

JSON:

```bash
a-facegroup identify ~/Pictures/NewPhoto.heic --json
```

Expected behaviour:

- Analyse the supplied image.
- Identify faces that match stored entities.
- Report unmatched faces as unmatched.
- Do not insert the image into the persistent gallery.
- Do not fabricate confidence values if the framework does not provide them.

### 4.5 Export photos by person

Preview:

```bash
a-facegroup export ~/Pictures/Sorted
```

Perform export:

```bash
a-facegroup export ~/Pictures/Sorted \
  --mode copy \
  --apply
```

Optional symbolic-link mode:

```bash
a-facegroup export ~/Pictures/Sorted \
  --mode symlink \
  --apply
```

Illustrative result:

```text
Sorted/
├── Person_001/
│   ├── IMG_001.HEIC
│   └── IMG_003.JPG
├── Person_002/
│   ├── IMG_002.HEIC
│   └── IMG_003.JPG
└── No_Faces/
    └── IMG_004.JPG
```

`IMG_003.JPG` belongs to two folders because the photo contains two different people.

The export planner must deduplicate repeated references to the same photo within one person folder.

Images with no detected faces should be distinguishable from faces that did not match an existing identity.

---

## 5. Repository Structure

Recommended structure:

```text
a-facegroup/
├── Package.swift
├── README.md
├── LICENSE
├── AGENTS.md
├── .gitignore
├── Sources/
│   ├── AFaceGroupCLI/
│   │   ├── main.swift
│   │   ├── ScanCommand.swift
│   │   ├── PeopleCommand.swift
│   │   ├── IdentifyCommand.swift
│   │   └── ExportCommand.swift
│   │
│   └── AFaceGroupCore/
│       ├── FaceGroupService.swift
│       ├── AssetScanner.swift
│       ├── AssetManifest.swift
│       ├── PhotoExporter.swift
│       ├── Models.swift
│       └── Errors.swift
│
├── Tests/
│   ├── AFaceGroupCoreTests/
│   └── AFaceGroupIntegrationTests/
│
└── docs/
    └── architecture.md
```

This is a proposed layout. Keep it simpler if fewer files are sufficient.

### Module responsibilities

**AFaceGroupCLI**

- Argument parsing
- Command routing
- JSON and human-readable formatting
- Validation and error reporting
- No direct face clustering implementation

**AFaceGroupCore**

- Business logic
- Stable asset manifest
- Photo discovery and metadata
- Export planning
- Testable domain models

**FaceGroupService**

- Dedicated wrapper around Apple `FaceGroupAnalyzer`
- Asynchronous ingestion and clustering
- Entity and face retrieval
- Read-only identification

**PhotoExporter**

- Calculate folder destinations.
- Handle filename collisions.
- Implement copy and symlink operations.
- Prevent overwrites and recursive processing.
- Support preview and explicit execution.

A protocol around the framework adapter is appropriate if it enables deterministic tests without requiring the real framework.

Avoid unnecessary abstractions.

---

## 6. Persistence Design

The Apple framework already persists its own face and clustering data.

Do not duplicate this internal data into a custom face database.

However, `a-facegroup` needs an application-owned asset manifest to map Apple asset identifiers to source paths.

### Suggested application data directory

```text
~/Library/Application Support/a-facegroup/
├── analyzer/
└── manifest.json
```

The `analyzer/` directory belongs exclusively to Apple.

The application owns `manifest.json`.

### Manifest responsibilities

Track:

- Asset ID
- Canonical source path
- File size
- Modification timestamp
- Optional content hash
- Indexing status and relevant metadata

### Asset identity

Do not use `lastPathComponent` alone as an asset ID.

Different directories can contain files with identical names.

Use persisted unique identifiers associated with canonical paths. If supporting renames or moves, establish and document a deliberate identity-reconciliation strategy.

For initial change detection, file size plus modification time is acceptable as a fast heuristic. Provide a way to force a full recheck when needed.

Do not automatically delete previously indexed assets merely because they are absent from one partial scan.

### Entity identifiers

Keep Apple entity identifiers separate from user-visible names.

A future version may introduce stable application-level person IDs and user-assigned names.

For v0.1.0, use the native entity identities and document any stability limitations. Do not persist long-lived display-name associations without first verifying identity behaviour across updates.

---

## 7. Edge Cases

The implementation must explicitly handle:

1. **Group photos:** One photo can belong to multiple people.
2. **Duplicate filenames:** Different source images must not overwrite one another.
3. **Repeat scans:** Unchanged images should not be reprocessed unnecessarily.
4. **Modified images:** Existing assets should be updated using their consistent IDs.
5. **Empty directories:** Return useful success output rather than crashing.
6. **No-face images:** Track and report separately.
7. **Unmatched faces:** Do not invent identities or similarity confidence.
8. **Corrupt or unsupported images:** Report failures without stopping the entire batch.
9. **Interrupted processing:** Resume safely and recover from stale analyzer state.
10. **Large collections:** Avoid loading all full-resolution images into memory simultaneously.
11. **Output path collisions:** Use deterministic, safe collision handling.
12. **Nested export directories:** Prevent recursive scan/export loops.
13. **Symlinks:** Define and test traversal behaviour; avoid directory cycles.
14. **Concurrent invocations:** Prevent two writing processes from mutating the same library simultaneously.

File scanning should support JPEG, PNG, and HEIC where validated by the platform. Additional formats can be added after verification.

Do not claim RAW support unless actual formats have been tested.

---

## 8. Testing Strategy

Use Swift Testing where appropriate.

### Unit tests

Test pure logic independently of Apple ML inference:

- Asset ID generation and persistence
- Recursive directory discovery
- Supported-file filtering
- Manifest updates
- Duplicate path handling
- Multiple people per photo
- Filename collision resolution
- Export path validation
- Dry-run correctness
- JSON schema consistency
- Error conversion and exit codes
- Interrupted-operation recovery logic

### Integration tests

On macOS 27+:

- Initialise a real `FaceGroupAnalyzer`.
- Insert sample images.
- Execute grouping.
- Retrieve entities and assets.
- Reopen the analyzer working directory.
- Add additional images and regroup.
- Identify a new image without storing it.
- Verify that original photos are unchanged.

Use small, licensed or consented test images.

### Evaluation

Maintain a separate, manually verified photo dataset to evaluate real-world clustering behaviour.

Report, where labels permit:

- False person merges
- False person splits
- Unmatched faces
- Processing throughput
- Peak memory consumption

Do not claim clustering accuracy based solely on successful framework calls or synthetic unit tests.

---

## 9. Implementation Phases

### Phase 0 — Framework validation

Before building the full application:

- Confirm macOS 27 SDK and runtime availability.
- Compile a minimal Swift executable importing `MediaIntelligence`.
- Verify `FaceGroupAnalyzer` initialisation.
- Insert a few local photos.
- Run `update()`.
- Retrieve entity and asset IDs.
- Verify persistence across launches.

**Deliverable:** A working proof of concept and documented API limitations.

If the required SDK or runtime is unavailable, do not replace the production engine with an unrelated ML library. Implement the pure core and mockable interfaces, and clearly report the unverified integration.

### Phase 1 — Core engine

Implement:

- `FaceGroupService`
- Photo discovery
- Asset manifest
- Incremental ingestion
- Face clustering
- Entity retrieval

**Deliverable:** Scan a directory and retrieve grouped results programmatically.

### Phase 2 — CLI

Implement:

- `scan`
- `people list`
- `people photos`
- `identify`
- `--json`
- `--help`
- `--version`

**Deliverable:** Working UNIX CLI with clean output and error handling.

### Phase 3 — Photo export

Implement:

- Export planning
- Safe copy mode
- Optional symlink mode
- Dry-run by default
- Explicit `--apply`
- Collision handling
- Group photo support

**Deliverable:** Non-destructive person-based folder organisation.

### Phase 4 — Release readiness

- Complete unit tests.
- Complete framework integration tests where possible.
- Validate clean installation.
- Write README and architecture documentation.
- Add GitHub Actions CI.
- Review dependency and framework requirements.
- Prepare v0.1.0 release instructions.

---

## 10. Explicit Non-Goals for v0.1.0

Do not implement:

- GUI or SwiftUI application
- REST API / HTTP server
- MCP server
- Python bindings
- Custom face recognition models
- DBSCAN / HDBSCAN / Chinese Whispers
- Custom face embedding database
- Cloud synchronisation
- Direct Apple Photos library integration
- Face embedding extraction
- Automatic person naming using an LLM
- Manual identity merge/split UI
- Multi-user identity sharing

These are potential future enhancements, not MVP requirements.

The initial objective is a small, reliable wrapper around Apple's native capabilities.

---

## 11. Documentation and Open Source Requirements

### README.md

Include:

- Project purpose
- Features and limitations
- macOS and Swift requirements
- Installation instructions
- CLI examples
- JSON output examples
- How persistent data works
- Privacy and security statement
- Safe export behaviour
- Development and testing instructions
- Attribution

Suggested attribution:

> Inspired by the UNIX philosophy and Arthur-Ficial's Apple-native CLI projects, including apfel and auge. a-facegroup is an independent open-source project and is not officially affiliated with those projects.

### AGENTS.md

Document:

- Golden Goal
- Architecture boundaries
- Swift 6 concurrency expectations
- Apple-native dependency preference
- CLI conventions
- Test requirements
- Safe filesystem rules
- Development and release workflow

Do not blindly copy another project's instructions.

### License

Use MIT for original project code.

If source code is copied or adapted from an existing project, preserve the applicable license notices and attribution.

---

## 12. Definition of Done — v0.1.0

The MVP is complete when:

- [ ] The project builds on a supported macOS 27 development environment.
- [ ] `a-facegroup --help` works.
- [ ] The CLI scans a directory of photos.
- [ ] The Apple framework detects and clusters faces.
- [ ] The application persists analysis between runs.
- [ ] Repeated scans avoid unnecessary processing.
- [ ] Users can list detected people and their photos.
- [ ] Users can identify known people in a new image without modifying the gallery.
- [ ] Group photos can appear in multiple people folders.
- [ ] Export previews are non-destructive.
- [ ] Explicit export creates the expected directory structure.
- [ ] Original photos remain unchanged.
- [ ] Duplicate filenames cannot silently overwrite existing files.
- [ ] Human-readable and JSON output work correctly.
- [ ] Unit and integration tests pass in their supported environments.
- [ ] README clearly documents limitations and privacy behaviour.

---

## 13. Instructions for the Coding Agent

You are responsible for implementing `a-facegroup` from scratch.

Follow these rules:

1. **Start by validating Apple's actual API.** Read official documentation and compile a minimal working example before designing a large abstraction.
2. Create an independent Swift package named `a-facegroup`.
3. Use the principles in this handoff as the architectural contract.
4. Keep domain logic, Apple framework integration, and CLI orchestration separate.
5. Prefer simplicity over speculative extensibility.
6. Use test-driven development for pure logic and filesystem operations.
7. Keep all original image files safe.
8. Do not claim unsupported Apple API functionality.
9. Do not implement features outside the MVP unless required for correctness.
10. Use conventional commits, with clear, focused changes.
11. Track implementation progress in a file-based plan or Kanban.
12. Record important architecture decisions in short ADRs only when a meaningful trade-off exists.
13. Verify claims through actual builds and tests wherever the local environment permits.
14. Do not claim macOS 27 integration is tested if the required SDK/runtime is unavailable.
15. Document limitations, missing test coverage, and remaining risks.

### Expected final output

Provide:

- Working Swift source code
- Package configuration
- Unit and integration tests
- README
- AGENTS.md
- Architecture documentation
- Build and test instructions
- Known limitations
- A concise implementation summary

**Begin with Phase 0: Apple MediaIntelligence API validation. Proceed through the MVP phases without introducing unnecessary infrastructure.**

The final implementation should feel like a small, carefully engineered Apple-native UNIX utility — not a full photo management application.
