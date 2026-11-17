# MVP implementation plan

- [x] Check Apple documentation and installed SDK signatures.
- [x] Validate native analyzer initialization and no-face scan persistence on macOS 27.
- [x] Validate detection, clustering, identification, and persistence with a public-domain NASA portrait.
- [x] Record small labeled clustering, held-out identification, and process-resource evaluations, including a public-figure set.
- [ ] Evaluate representative real-world clustering, throughput, and total memory with a larger labeled collection.
- [x] Add hosted CI compilation using the Xcode 27 runner. Runtime tests still require macOS 27.
- [x] Implement incremental scanning, retrieval, identification, and safe export.
- [x] Run unit tests and CLI verification; document limitations.
- [x] Prepare pull request.
