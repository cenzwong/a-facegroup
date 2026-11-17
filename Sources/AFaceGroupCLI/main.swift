import Foundation
import AFaceGroupCore
import Darwin

let help = """
a-facegroup 0.1.0
Usage: a-facegroup <command> [options]
  scan <directory> [--recursive] [--force] [--json] [--quiet]
  people list [--json] [--quiet]
  people photos <person-id> [--json] [--quiet]
  identify <image> [--json] [--quiet]
  export <directory> [--mode copy|symlink] [--apply] [--json] [--quiet]
  --help  --version
Scans recurse without following symlinks. Export is preview-only unless --apply is given.
"""
struct PeopleOutput: Encodable { let people: [Person]; let totalPeople: Int }
struct PhotosOutput: Encodable { let personID: String; let photos: [String] }
struct IdentifyOutput: Encodable { let faces: [Identification]; let totalFaces: Int }
struct ExportOutput: Encodable { let applied: Bool; let mode: String; let items: [ExportItem] }
func output<T: Encodable>(_ value: T, json: Bool, quiet: Bool, stdoutFD: Int32, human: () -> String) throws {
    fflush(nil); _ = dup2(stdoutFD, STDOUT_FILENO); close(stdoutFD)
    if json { let e = JSONEncoder(); e.outputFormatting = [.prettyPrinted, .sortedKeys]; e.keyEncodingStrategy = .convertToSnakeCase; print(String(decoding: try e.encode(value), as: UTF8.self)) }
    else if !quiet { print(human()) }
}
@main struct Main {
    static func main() async {
        do { try await run() } catch { fputs("error: \(error.localizedDescription)\n", stderr); exit(1) }
    }
    static func run() async throws {
        var args = Array(CommandLine.arguments.dropFirst())
        if args == ["--help"] || args == ["-h"] { print(help); return }
        if args == ["--version"] { print("0.1.0"); return }
        guard !args.isEmpty else { throw Failure("Missing command; use --help") }
        let json = args.contains("--json"), quiet = args.contains("--quiet")
        args.removeAll { $0 == "--json" || $0 == "--quiet" }
        let command = args.removeFirst()
        var mode = "copy", apply = false, force = false, recursive = false, positional: [String] = []
        while !args.isEmpty {
            let arg = args.removeFirst()
            switch arg {
            case "--mode": guard !args.isEmpty else { throw Failure("--mode requires a value") }; mode = args.removeFirst()
            case "--apply": apply = true
            case "--force": force = true
            case "--recursive": recursive = true
            default: if arg.hasPrefix("-") { throw Failure("Unknown option: \(arg)") }; positional.append(arg)
            }
        }
        guard ["copy", "symlink"].contains(mode) else { throw Failure("Mode must be copy or symlink") }
        guard (command == "scan" || (!force && !recursive)), (command == "export" || (!apply && mode == "copy")) else { throw Failure("Option is not valid for \(command)") }
        let data = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("a-facegroup", isDirectory: true)
        // A custom location makes separate libraries and isolated testing possible.
        let directory = ProcessInfo.processInfo.environment["AFACEGROUP_HOME"].map { URL(fileURLWithPath: $0, isDirectory: true) } ?? data
        // MediaIntelligence emits diagnostics on stdout; reserve stdout for results.
        let stdoutFD = dup(STDOUT_FILENO)
        guard stdoutFD >= 0, dup2(STDERR_FILENO, STDOUT_FILENO) >= 0 else { throw Failure("Cannot redirect framework diagnostics") }
        switch command {
        case "scan":
            guard positional.count == 1 else { throw Failure("Usage: scan <directory>") }
            let service = try FaceService(directory: directory); let result = try await service.scan(URL(fileURLWithPath: positional[0]), force: force)
            try output(result, json: json, quiet: quiet, stdoutFD: stdoutFD) { "Processed: \(result.processed), skipped: \(result.skipped), no faces: \(result.noFaces), failed: \(result.failures.count)\n" + result.failures.joined(separator: "\n") }
            if !result.failures.isEmpty { exit(1) }
        case "people":
            guard positional.count == 1 && positional[0] == "list" || positional.count == 2 && positional[0] == "photos" else { throw Failure("Usage: people list | people photos <person-id>") }
            let people = try await FaceService(directory: directory).people()
            if positional[0] == "list" { try output(PeopleOutput(people: people, totalPeople: people.count), json: json, quiet: quiet, stdoutFD: stdoutFD) { people.map { "\($0.id)  faces: \($0.faceCount)  photos: \($0.photoCount)" }.joined(separator: "\n") } }
            else { guard let person = people.first(where: { $0.id == positional[1] }) else { throw Failure("Unknown person ID") }; try output(PhotosOutput(personID: person.id, photos: person.paths), json: json, quiet: quiet, stdoutFD: stdoutFD) { person.paths.joined(separator: "\n") } }
        case "identify":
            guard positional.count == 1 else { throw Failure("Usage: identify <image>") }
            let faces = try await FaceService(directory: directory).identify(URL(fileURLWithPath: positional[0]))
            try output(IdentifyOutput(faces: faces, totalFaces: faces.count), json: json, quiet: quiet, stdoutFD: stdoutFD) { faces.isEmpty ? "No faces detected" : faces.map { $0.entityID ?? "unmatched" }.joined(separator: "\n") }
        case "export":
            guard positional.count == 1 else { throw Failure("Usage: export <directory>") }
            let service = try FaceService(directory: directory); let plan = try await service.planExport(URL(fileURLWithPath: positional[0]))
            if apply { try applyExport(plan, mode: mode) }
            try output(ExportOutput(applied: apply, mode: mode, items: plan), json: json, quiet: quiet, stdoutFD: stdoutFD) { (apply ? "Exported" : "Preview") + ":\n" + plan.map { "\($0.source) -> \($0.destination)" }.joined(separator: "\n") }
        default: throw Failure("Unknown command: \(command)")
        }
    }
}
