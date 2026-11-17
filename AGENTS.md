# Project guidance

Build a small, privacy-first UNIX CLI exposing Apple's on-device FaceGroupAnalyzer for non-destructive photo organization. Before implementing a solution, identify the user's underlying objective and evaluate whether the approach is the simplest reliable one; explain material trade-offs briefly. Do not assume permissions.

Keep CLI parsing and output separate from filesystem logic and the MediaIntelligence adapter. Prefer Apple frameworks and Swift 6 strict concurrency. Never access the analyzer's private storage directly or invent framework capabilities. Keep JSON on stdout and diagnostics on stderr. Preserve source photos; exports must preview by default, require `--apply`, avoid overwrites and reject overlapping directories. Do not follow scan symlinks.

Run focused unit tests and native builds for changes; report separately what has and has not been tested with real images. Track work in docs/plan.md and document meaningful architectural decisions. Use conventional commits and keep releases and PRs reviewable.
